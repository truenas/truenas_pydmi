"""Per-type SMBIOS structure parsers.

Each parser takes a :class:`models.RawStructure` and returns a typed
dataclass. They are pure functions: no I/O, no caching, no global state.

Field offsets in this file are given relative to the *formatted area*
(``RawStructure.formatted``), which is everything after the 4-byte
type/length/handle header. SMBIOS spec offsets are 4 bytes higher.
"""

from __future__ import annotations

from datetime import date, datetime
import struct
from uuid import UUID

from . import models


def _str(strings: tuple[str, ...], index: int) -> str:
    """Resolve a 1-based SMBIOS string index. ``0`` means 'no string'."""
    if index == 0 or index > len(strings):
        return ""
    return strings[index - 1]


def _u8(buf: bytes, offset: int) -> int | None:
    return buf[offset] if offset < len(buf) else None


def _u16(buf: bytes, offset: int) -> int | None:
    if offset + 2 > len(buf):
        return None
    return struct.unpack_from("<H", buf, offset)[0]


def _u32(buf: bytes, offset: int) -> int | None:
    if offset + 4 > len(buf):
        return None
    return struct.unpack_from("<I", buf, offset)[0]


def _u64(buf: bytes, offset: int) -> int | None:
    if offset + 8 > len(buf):
        return None
    return struct.unpack_from("<Q", buf, offset)[0]


def _decode_extended_size(value: int | None) -> int | None:
    """SMBIOS extended memory-device size fields use all-1s as the 'unknown'
    sentinel. Returns ``None`` for unknown, the value itself otherwise."""
    if value is None or value == 0xFFFFFFFFFFFFFFFF:
        return None
    return value


def _parse_bios_release_date(s: str) -> date | None:
    """SMBIOS BIOS Release Date format is ``MM/DD/YYYY`` (sometimes ``MM/DD/YY``)."""
    s = s.strip()
    if not s:
        return None
    parts = s.split("/")
    if len(parts) != 3:
        return None
    fmt = "%m/%d/%Y" if len(parts[-1]) == 4 else "%m/%d/%y"
    try:
        return datetime.strptime(s, fmt).date()
    except ValueError:
        return None


def parse_bios(raw: models.RawStructure) -> models.BIOSInfo:
    """Parse a SMBIOS Type 0 (BIOS Information) structure into a :class:`models.BIOSInfo`."""
    f = raw.formatted
    s = raw.strings

    vendor = _str(s, _u8(f, 0) or 0)
    version = _str(s, _u8(f, 1) or 0)
    # f[2:4] = BIOS starting segment (skip)
    release_date_raw = _str(s, _u8(f, 4) or 0)
    release_date = _parse_bios_release_date(release_date_raw)
    rom_size = _u8(f, 5)
    rom_size_bytes: int | None = None
    if rom_size is not None:
        if rom_size == 0xFF:
            # SMBIOS 3.1+: legacy byte is 0xFF, read Extended BIOS ROM Size
            # (16-bit word at spec offset 24 / formatted offset 20):
            # bits 0-13 = size value, bits 14-15 = unit (00=MB, 01=GB).
            extended = _u16(f, 20)
            if extended is not None and extended != 0:
                size_value = extended & 0x3FFF
                unit = (extended >> 14) & 0x03
                if unit == 0:
                    rom_size_bytes = size_value * 1024 * 1024
                elif unit == 1:
                    rom_size_bytes = size_value * 1024 * 1024 * 1024
            else:
                # Pre-3.1 BIOS or extended field missing: 0xFF in the legacy
                # byte means "size is 16 MB or greater" per the spec, so
                # report the implied floor (the same fallback dmidecode uses).
                rom_size_bytes = 16 * 1024 * 1024
        else:
            rom_size_bytes = (rom_size + 1) * 65536
    characteristics = _u64(f, 6) or 0

    # Extension bytes start at formatted offset 14 (spec offset 18)
    bios_major = _u8(f, 16)
    bios_minor = _u8(f, 17)
    ec_major = _u8(f, 18)
    ec_minor = _u8(f, 19)
    characteristics_extension = bytes(f[14:])

    return models.BIOSInfo(
        handle=raw.handle,
        vendor=vendor,
        version=version,
        release_date=release_date,
        release_date_raw=release_date_raw,
        rom_size_bytes=rom_size_bytes,
        bios_major=bios_major,
        bios_minor=bios_minor,
        ec_major=ec_major,
        ec_minor=ec_minor,
        characteristics=characteristics,
        characteristics_extension=characteristics_extension,
    )


def _parse_uuid(buf: bytes) -> UUID | None:
    """Parse a 16-byte SMBIOS UUID. SMBIOS 2.6+ uses little-endian byte order
    for the first three fields (matching Microsoft GUID convention); older
    SMBIOS used pure big-endian. We use little-endian since 2.6 was 2007 and
    every system we care about is well past that. All-zero is treated as
    'not set'; all-FF is preserved verbatim."""
    if len(buf) < 16:
        return None
    raw = bytes(buf[:16])
    if raw == b"\x00" * 16:
        return None
    try:
        return UUID(bytes_le=raw)
    except ValueError:
        return None


def parse_system(raw: models.RawStructure) -> models.SystemInfo:
    """Parse a SMBIOS Type 1 (System Information) structure into a :class:`models.SystemInfo`."""
    f = raw.formatted
    s = raw.strings

    manufacturer = _str(s, _u8(f, 0) or 0)
    product_name = _str(s, _u8(f, 1) or 0)
    version = _str(s, _u8(f, 2) or 0)
    serial_number = _str(s, _u8(f, 3) or 0)
    uuid = _parse_uuid(f[4:20]) if len(f) >= 20 else None
    wake_up_type = _u8(f, 20) or 0
    sku_number = _str(s, _u8(f, 21) or 0)
    family = _str(s, _u8(f, 22) or 0)

    return models.SystemInfo(
        handle=raw.handle,
        manufacturer=manufacturer,
        product_name=product_name,
        version=version,
        serial_number=serial_number,
        uuid=uuid,
        wake_up_type=wake_up_type,
        sku_number=sku_number,
        family=family,
    )


def parse_baseboard(raw: models.RawStructure) -> models.BaseboardInfo:
    """Parse a SMBIOS Type 2 (Baseboard) structure into a :class:`models.BaseboardInfo`."""
    f = raw.formatted
    s = raw.strings

    return models.BaseboardInfo(
        handle=raw.handle,
        manufacturer=_str(s, _u8(f, 0) or 0),
        product=_str(s, _u8(f, 1) or 0),
        version=_str(s, _u8(f, 2) or 0),
        serial_number=_str(s, _u8(f, 3) or 0),
        asset_tag=_str(s, _u8(f, 4) or 0),
        feature_flags=_u8(f, 5) or 0,
        location_in_chassis=_str(s, _u8(f, 6) or 0),
        chassis_handle=_u16(f, 7) or 0,
        board_type=_u8(f, 9) or 0,
    )


def parse_chassis(raw: models.RawStructure) -> models.ChassisInfo:
    """Parse a SMBIOS Type 3 (Chassis) structure into a :class:`models.ChassisInfo`."""
    f = raw.formatted
    s = raw.strings

    type_byte = _u8(f, 1) or 0
    type_locked = bool(type_byte & 0x80)
    chassis_type = type_byte & 0x7F

    height = _u8(f, 13)
    if height == 0:
        height = None
    power_cords = _u8(f, 14)
    if power_cords == 0:
        power_cords = None

    # SKU Number string index sits after the contained-element table.
    # Element count at f[15], element record length at f[16],
    # so SKU index lives at f[17 + n*m] (SMBIOS 2.7+).
    n = _u8(f, 15) or 0
    m = _u8(f, 16) or 0
    sku_offset = 17 + n * m
    sku_idx = _u8(f, sku_offset) or 0
    sku_number = _str(s, sku_idx)

    return models.ChassisInfo(
        handle=raw.handle,
        manufacturer=_str(s, _u8(f, 0) or 0),
        type=chassis_type,
        type_locked=type_locked,
        version=_str(s, _u8(f, 2) or 0),
        serial_number=_str(s, _u8(f, 3) or 0),
        asset_tag=_str(s, _u8(f, 4) or 0),
        bootup_state=_u8(f, 5) or 0,
        power_supply_state=_u8(f, 6) or 0,
        thermal_state=_u8(f, 7) or 0,
        security_status=_u8(f, 8) or 0,
        height_u=height,
        power_cords=power_cords,
        sku_number=sku_number,
    )


def parse_processor(raw: models.RawStructure) -> models.ProcessorInfo:
    """Parse a SMBIOS Type 4 (Processor Information) structure into a :class:`models.ProcessorInfo`."""
    f = raw.formatted
    s = raw.strings

    # The 8-bit Family field can be 0xFE meaning "see Family 2 at offset 36"
    family_8 = _u8(f, 2) or 0
    family_16 = _u16(f, 36)
    family = family_16 if family_8 == 0xFE and family_16 is not None else family_8

    # Speeds: 0 means unknown
    ext_clock = _u16(f, 14)
    max_speed = _u16(f, 16)
    cur_speed = _u16(f, 18)
    if ext_clock == 0:
        ext_clock = None
    if max_speed == 0:
        max_speed = None
    if cur_speed == 0:
        cur_speed = None

    # Cache handles. SMBIOS uses 0xFFFF as the "no cache / not provided" sentinel.
    l1_cache = _u16(f, 22)
    l2_cache = _u16(f, 24)
    l3_cache = _u16(f, 26)
    if l1_cache == 0xFFFF:
        l1_cache = None
    if l2_cache == 0xFFFF:
        l2_cache = None
    if l3_cache == 0xFFFF:
        l3_cache = None

    # Core/thread counts: 0xFF means "see Core Count 2/Thread Count 2"
    core_count_8 = _u8(f, 31)
    core_enabled_8 = _u8(f, 32)
    thread_count_8 = _u8(f, 33)
    core_count_16 = _u16(f, 38)
    core_enabled_16 = _u16(f, 40)
    thread_count_16 = _u16(f, 42)
    threads_enabled_16 = _u16(f, 44)

    def _resolve(small: int | None, big: int | None) -> int | None:
        if small is None:
            return None
        if small == 0xFF and big is not None:
            return big
        if small == 0:
            return None
        return small

    core_count = _resolve(core_count_8, core_count_16)
    cores_enabled = _resolve(core_enabled_8, core_enabled_16)
    thread_count = _resolve(thread_count_8, thread_count_16)
    # threads_enabled has no 8-bit counterpart; only present in SMBIOS 3.6+
    threads_enabled = threads_enabled_16 if threads_enabled_16 not in (None, 0) else None

    processor_id = bytes(f[4:12]) if len(f) >= 12 else b""

    return models.ProcessorInfo(
        handle=raw.handle,
        socket_designation=_str(s, _u8(f, 0) or 0),
        type=_u8(f, 1) or 0,
        family=family,
        manufacturer=_str(s, _u8(f, 3) or 0),
        processor_id=processor_id,
        version=_str(s, _u8(f, 12) or 0),
        voltage_raw=_u8(f, 13) or 0,
        external_clock_mhz=ext_clock,
        max_speed_mhz=max_speed,
        current_speed_mhz=cur_speed,
        status=_u8(f, 20) or 0,
        upgrade=_u8(f, 21) or 0,
        l1_cache_handle=l1_cache,
        l2_cache_handle=l2_cache,
        l3_cache_handle=l3_cache,
        serial_number=_str(s, _u8(f, 28) or 0),
        asset_tag=_str(s, _u8(f, 29) or 0),
        part_number=_str(s, _u8(f, 30) or 0),
        core_count=core_count,
        cores_enabled=cores_enabled,
        thread_count=thread_count,
        threads_enabled=threads_enabled,
        characteristics=_u16(f, 34) or 0,
    )


def _decode_cache_size(value: int | None, value2: int | None) -> int | None:
    """Decode the SMBIOS cache size encoding.
    16-bit field: bit 15 = granularity (0 = 1 KB, 1 = 64 KB), bits 0-14 = size.
    If the 16-bit field is 0xFFFF the 32-bit Cache Size 2 field is used
    (bit 31 = granularity, bits 0-30 = size). Returns ``None`` if size
    is unknown or missing."""
    if value is None:
        return None
    if value == 0:
        return 0
    if value == 0xFFFF:
        if value2 is None or value2 == 0:
            return None
        granularity = 65536 if (value2 & 0x80000000) else 1024
        size = value2 & 0x7FFFFFFF
        return size * granularity
    granularity = 65536 if (value & 0x8000) else 1024
    size = value & 0x7FFF
    return size * granularity


def parse_cache(raw: models.RawStructure) -> models.CacheInfo:
    """Parse a SMBIOS Type 7 (Cache Information) structure into a :class:`models.CacheInfo`."""
    f = raw.formatted
    s = raw.strings

    max_size = _u16(f, 3)
    installed_size = _u16(f, 5)
    max_size_2 = _u32(f, 15)
    installed_size_2 = _u32(f, 19)

    speed = _u8(f, 11)
    if speed == 0:
        speed = None

    return models.CacheInfo(
        handle=raw.handle,
        socket_designation=_str(s, _u8(f, 0) or 0),
        configuration=_u16(f, 1) or 0,
        max_size_bytes=_decode_cache_size(max_size, max_size_2),
        installed_size_bytes=_decode_cache_size(installed_size, installed_size_2),
        supported_sram_types=_u16(f, 7) or 0,
        current_sram_type=_u16(f, 9) or 0,
        speed_nanoseconds=speed,
        error_correction=_u8(f, 12) or 0,
        system_cache_type=_u8(f, 13) or 0,
        associativity=_u8(f, 14) or 0,
    )


def parse_system_slot(raw: models.RawStructure) -> models.SystemSlot:
    """Parse a SMBIOS Type 9 (System Slot) structure into a :class:`models.SystemSlot`."""
    f = raw.formatted
    s = raw.strings

    return models.SystemSlot(
        handle=raw.handle,
        designation=_str(s, _u8(f, 0) or 0),
        type=_u8(f, 1) or 0,
        bus_width=_u8(f, 2) or 0,
        current_usage=_u8(f, 3) or 0,
        length=_u8(f, 4) or 0,
        slot_id=_u16(f, 5) or 0,
        characteristics_1=_u8(f, 7) or 0,
        characteristics_2=_u8(f, 8) or 0,
        segment_group=_u16(f, 9),
        bus_number=_u8(f, 11),
        device_function=_u8(f, 12),
    )


def parse_oem_strings(raw: models.RawStructure) -> tuple[str, ...]:
    """Type 11 is just a count + the structure's own string table."""
    return raw.strings


def parse_memory_array(raw: models.RawStructure) -> models.MemoryArray:
    """Parse a SMBIOS Type 16 (Physical Memory Array) structure into a :class:`models.MemoryArray`."""
    f = raw.formatted

    max_capacity_kb = _u32(f, 3)
    extended_max_capacity = _u64(f, 11)

    if max_capacity_kb is not None and max_capacity_kb != 0x80000000:
        max_capacity_bytes: int | None = max_capacity_kb * 1024
    elif extended_max_capacity is not None and extended_max_capacity > 0:
        max_capacity_bytes = extended_max_capacity
    else:
        max_capacity_bytes = None

    return models.MemoryArray(
        handle=raw.handle,
        location=_u8(f, 0) or 0,
        use=_u8(f, 1) or 0,
        error_correction=_u8(f, 2) or 0,
        max_capacity_bytes=max_capacity_bytes,
        error_info_handle=_u16(f, 7) or 0,
        device_count=_u16(f, 9) or 0,
    )


def _decode_memory_size(size_word: int | None, extended_size: int | None) -> int | None:
    """SMBIOS Type 17 size encoding:
    - 0x0000 : empty slot (no module installed)        → 0
    - 0xFFFF : size unknown                            → None
    - 0x7FFF : use Extended Size (32-bit, in MB)
    - bit 15 == 1 : (size & 0x7FFF) is in KB
    - bit 15 == 0 : value is in MB
    """
    if size_word is None:
        return None
    if size_word == 0xFFFF:
        return None
    if size_word == 0:
        return 0
    if size_word == 0x7FFF:
        if extended_size is None or extended_size == 0:
            return None
        return extended_size * 1024 * 1024
    if size_word & 0x8000:
        return (size_word & 0x7FFF) * 1024
    return size_word * 1024 * 1024


def parse_memory_device(raw: models.RawStructure) -> models.MemoryDevice:
    """Parse a SMBIOS Type 17 (Memory Device) structure into a :class:`models.MemoryDevice`."""
    f = raw.formatted
    s = raw.strings

    total_width = _u16(f, 4)
    data_width = _u16(f, 6)
    size_word = _u16(f, 8)
    extended_size = _u32(f, 24)
    if total_width == 0xFFFF:
        total_width = None
    if data_width == 0xFFFF:
        data_width = None
    size_bytes = _decode_memory_size(size_word, extended_size)

    speed = _u16(f, 17)
    if speed == 0:
        speed = None
    configured_speed = _u16(f, 28)
    if configured_speed == 0:
        configured_speed = None

    rank_byte = _u8(f, 23)
    rank = (rank_byte & 0x0F) if rank_byte is not None and (rank_byte & 0x0F) else None

    min_v = _u16(f, 30)
    max_v = _u16(f, 32)
    cfg_v = _u16(f, 34)
    if min_v == 0:
        min_v = None
    if max_v == 0:
        max_v = None
    if cfg_v == 0:
        cfg_v = None

    # SMBIOS 3.2+ extensions (formatted offset 36 onward)
    memory_technology = _u8(f, 36) or 0
    operating_mode = _u16(f, 37) or 0
    module_fw = _str(s, _u8(f, 39) or 0)
    module_mfg_id = _u16(f, 40) or 0
    module_prod_id = _u16(f, 42) or 0
    subsys_mfg_id = _u16(f, 44) or 0
    subsys_prod_id = _u16(f, 46) or 0
    non_volatile_size = _decode_extended_size(_u64(f, 48))
    volatile_size = _decode_extended_size(_u64(f, 56))
    cache_size = _decode_extended_size(_u64(f, 64))
    logical_size = _decode_extended_size(_u64(f, 72))

    # SMBIOS 3.3+ extensions (formatted offset 80 onward). Bit 31 is reserved.
    extended_speed = _u32(f, 80)
    extended_cfg_speed = _u32(f, 84)
    if extended_speed is not None:
        extended_speed = extended_speed & 0x7FFFFFFF
        if extended_speed == 0:
            extended_speed = None
    if extended_cfg_speed is not None:
        extended_cfg_speed = extended_cfg_speed & 0x7FFFFFFF
        if extended_cfg_speed == 0:
            extended_cfg_speed = None

    return models.MemoryDevice(
        handle=raw.handle,
        array_handle=_u16(f, 0) or 0,
        error_info_handle=_u16(f, 2) or 0,
        total_width_bits=total_width,
        data_width_bits=data_width,
        size_bytes=size_bytes,
        form_factor=_u8(f, 10) or 0,
        device_set=_u8(f, 11) or 0,
        locator=_str(s, _u8(f, 12) or 0),
        bank_locator=_str(s, _u8(f, 13) or 0),
        type=_u8(f, 14) or 0,
        type_detail=_u16(f, 15) or 0,
        speed_mts=speed,
        manufacturer=_str(s, _u8(f, 19) or 0),
        serial_number=_str(s, _u8(f, 20) or 0),
        asset_tag=_str(s, _u8(f, 21) or 0),
        part_number=_str(s, _u8(f, 22) or 0),
        rank=rank,
        configured_speed_mts=configured_speed,
        min_voltage_mv=min_v,
        max_voltage_mv=max_v,
        configured_voltage_mv=cfg_v,
        memory_technology=memory_technology,
        operating_mode_capability=operating_mode,
        module_firmware_version=module_fw,
        module_manufacturer_id=module_mfg_id,
        module_product_id=module_prod_id,
        subsystem_controller_manufacturer_id=subsys_mfg_id,
        subsystem_controller_product_id=subsys_prod_id,
        non_volatile_size_bytes=non_volatile_size,
        volatile_size_bytes=volatile_size,
        cache_size_bytes=cache_size,
        logical_size_bytes=logical_size,
        extended_speed_mts=extended_speed,
        extended_configured_speed_mts=extended_cfg_speed,
    )


def parse_ipmi_device(raw: models.RawStructure) -> models.IPMIDevice:
    """Parse a SMBIOS Type 38 (IPMI Device Information) structure into a :class:`models.IPMIDevice`."""
    f = raw.formatted

    spec_byte = _u8(f, 1) or 0
    spec_major = (spec_byte >> 4) & 0x0F
    spec_minor = spec_byte & 0x0F

    return models.IPMIDevice(
        handle=raw.handle,
        interface_type=_u8(f, 0) or 0,
        spec_version_major=spec_major,
        spec_version_minor=spec_minor,
        i2c_slave_address=_u8(f, 2) or 0,
        nv_storage_address=_u8(f, 3) or 0,
        base_address=_u64(f, 4) or 0,
        base_address_modifier=_u8(f, 12) or 0,
        interrupt_number=_u8(f, 13) or 0,
    )


def parse_tpm_device(raw: models.RawStructure) -> models.TPMDevice:
    """Parse a SMBIOS Type 43 (TPM Device) structure into a :class:`models.TPMDevice`."""
    f = raw.formatted
    s = raw.strings

    # Vendor ID is 4 ASCII bytes. Strip nulls and decode.
    vendor_bytes = bytes(f[0:4]) if len(f) >= 4 else b""
    vendor_id = vendor_bytes.rstrip(b"\x00").decode("latin-1", errors="replace")

    return models.TPMDevice(
        handle=raw.handle,
        vendor_id=vendor_id,
        spec_major=_u8(f, 4) or 0,
        spec_minor=_u8(f, 5) or 0,
        firmware_version_1=_u32(f, 6) or 0,
        firmware_version_2=_u32(f, 10) or 0,
        description=_str(s, _u8(f, 14) or 0),
        characteristics=_u64(f, 15) or 0,
    )
