"""Typed dataclasses for SMBIOS structures."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from truenas_pydmi import enums


@dataclass(slots=True, frozen=True, kw_only=True)
class RawStructure:
    """A SMBIOS structure with its formatted area and string table parsed
    out, but not interpreted. Used internally and exposed via
    ``dmi.raw_structures()``."""

    type: int
    handle: int
    formatted: bytes
    strings: tuple[str, ...]


@dataclass(slots=True, frozen=True, kw_only=True)
class BIOSInfo:
    """SMBIOS Type 0 — BIOS Information."""

    handle: int
    vendor: str
    version: str
    release_date: date | None
    release_date_raw: str
    rom_size_bytes: int | None
    bios_major: int | None
    bios_minor: int | None
    ec_major: int | None
    ec_minor: int | None
    characteristics: int
    characteristics_extension: bytes

    @property
    def characteristics_decoded(self) -> tuple[str, ...]:
        """Human-readable feature names from the 64-bit characteristics
        qword and any extension bytes (e.g. 'PCI supported', 'UEFI
        Specification supported')."""
        return enums.bios_characteristics_names(self.characteristics, self.characteristics_extension)


@dataclass(slots=True, frozen=True, kw_only=True)
class SystemInfo:
    """SMBIOS Type 1 — System Information."""

    handle: int
    manufacturer: str
    product_name: str
    version: str
    serial_number: str
    uuid: UUID | None
    wake_up_type: int
    sku_number: str
    family: str


@dataclass(slots=True, frozen=True, kw_only=True)
class BaseboardInfo:
    """SMBIOS Type 2 — Baseboard (or Module) Information."""

    handle: int
    manufacturer: str
    product: str
    version: str
    serial_number: str
    asset_tag: str
    feature_flags: int
    location_in_chassis: str
    chassis_handle: int
    board_type: int


@dataclass(slots=True, frozen=True, kw_only=True)
class ChassisInfo:
    """SMBIOS Type 3 — System Enclosure or Chassis."""

    handle: int
    manufacturer: str
    type: int
    type_locked: bool
    version: str
    serial_number: str
    asset_tag: str
    bootup_state: int
    power_supply_state: int
    thermal_state: int
    security_status: int
    height_u: int | None
    power_cords: int | None
    sku_number: str


@dataclass(slots=True, frozen=True, kw_only=True)
class ProcessorInfo:
    """SMBIOS Type 4 — Processor Information."""

    handle: int
    socket_designation: str
    type: int
    family: int
    manufacturer: str
    processor_id: bytes
    version: str
    voltage_raw: int
    external_clock_mhz: int | None
    max_speed_mhz: int | None
    current_speed_mhz: int | None
    status: int
    upgrade: int
    l1_cache_handle: int | None
    l2_cache_handle: int | None
    l3_cache_handle: int | None
    serial_number: str
    asset_tag: str
    part_number: str
    core_count: int | None
    cores_enabled: int | None
    thread_count: int | None
    threads_enabled: int | None
    characteristics: int

    @property
    def populated(self) -> bool:
        """CPU Socket Populated bit (Status, bit 6)."""
        return bool(self.status & 0x40)

    @property
    def voltage_volts(self) -> float | None:
        """Decoded operating voltage in volts. Returns the current voltage
        in modern mode (bit 7 of voltage_raw set, value in tenths of V),
        or the highest of the supported voltages in legacy mode (bit 7
        clear, bits 0-3 are flags for 5V / 3.3V / 2.9V). ``None`` if
        voltage_raw is 0 (unknown)."""
        if self.voltage_raw == 0:
            return None
        if self.voltage_raw & 0x80:
            return (self.voltage_raw & 0x7F) / 10.0
        if self.voltage_raw & 0x01:
            return 5.0
        if self.voltage_raw & 0x02:
            return 3.3
        if self.voltage_raw & 0x04:
            return 2.9
        return None


@dataclass(slots=True, frozen=True, kw_only=True)
class CacheInfo:
    """SMBIOS Type 7 — Cache Information.

    Look up by handle from ``ProcessorInfo.l1_cache_handle`` /
    ``l2_cache_handle`` / ``l3_cache_handle`` via :func:`cache`."""

    handle: int
    socket_designation: str
    configuration: int
    max_size_bytes: int | None
    installed_size_bytes: int | None
    supported_sram_types: int
    current_sram_type: int
    speed_nanoseconds: int | None
    error_correction: int
    system_cache_type: int
    associativity: int

    @property
    def cache_level(self) -> int:
        """1-based cache level (1 for L1, 2 for L2, ...). Stored as bits
        0-2 of the configuration word with the value (level - 1)."""
        return (self.configuration & 0x07) + 1

    @property
    def socketed(self) -> bool:
        """Bit 3 of the configuration word."""
        return bool(self.configuration & 0x08)

    @property
    def enabled_at_boot(self) -> bool:
        """Bit 7 of the configuration word."""
        return bool(self.configuration & 0x80)

    @property
    def location_name(self) -> str:
        """Cache location relative to the CPU module (bits 5-6 of
        configuration): Internal, External, Reserved, or Unknown."""
        return enums.cache_location_name((self.configuration >> 5) & 0x03)

    @property
    def operational_mode_name(self) -> str:
        """Write Through / Write Back / Varies / Unknown
        (bits 8-9 of configuration)."""
        return enums.cache_operational_mode_name((self.configuration >> 8) & 0x03)

    @property
    def error_correction_name(self) -> str:
        return enums.cache_error_correction_name(self.error_correction)

    @property
    def system_cache_type_name(self) -> str:
        return enums.cache_system_type_name(self.system_cache_type)

    @property
    def associativity_name(self) -> str:
        return enums.cache_associativity_name(self.associativity)

    @property
    def supported_sram_type_names(self) -> tuple[str, ...]:
        return enums.cache_sram_type_names(self.supported_sram_types)

    @property
    def current_sram_type_names(self) -> tuple[str, ...]:
        return enums.cache_sram_type_names(self.current_sram_type)


@dataclass(slots=True, frozen=True, kw_only=True)
class SystemSlot:
    """SMBIOS Type 9 — System Slots."""

    handle: int
    designation: str
    type: int
    bus_width: int
    current_usage: int
    length: int
    slot_id: int
    characteristics_1: int
    characteristics_2: int
    segment_group: int | None
    bus_number: int | None
    device_function: int | None


@dataclass(slots=True, frozen=True, kw_only=True)
class MemoryArray:
    """SMBIOS Type 16 — Physical Memory Array."""

    handle: int
    location: int
    use: int
    error_correction: int
    max_capacity_bytes: int | None
    error_info_handle: int
    device_count: int


@dataclass(slots=True, frozen=True, kw_only=True)
class MemoryDevice:
    """SMBIOS Type 17 — Memory Device."""

    handle: int
    array_handle: int
    error_info_handle: int
    total_width_bits: int | None
    data_width_bits: int | None
    size_bytes: int | None
    form_factor: int
    device_set: int
    locator: str
    bank_locator: str
    type: int
    type_detail: int
    speed_mts: int | None
    manufacturer: str
    serial_number: str
    asset_tag: str
    part_number: str
    rank: int | None
    configured_speed_mts: int | None
    min_voltage_mv: int | None
    max_voltage_mv: int | None
    configured_voltage_mv: int | None
    # SMBIOS 3.2+ extensions
    memory_technology: int
    operating_mode_capability: int
    module_firmware_version: str
    module_manufacturer_id: int
    module_product_id: int
    subsystem_controller_manufacturer_id: int
    subsystem_controller_product_id: int
    non_volatile_size_bytes: int | None
    volatile_size_bytes: int | None
    cache_size_bytes: int | None
    logical_size_bytes: int | None
    # SMBIOS 3.3+ extensions
    extended_speed_mts: int | None
    extended_configured_speed_mts: int | None

    @property
    def populated(self) -> bool:
        """A non-zero size_bytes means a module is installed."""
        return self.size_bytes is not None and self.size_bytes > 0

    @property
    def memory_technology_name(self) -> str:
        return enums.memory_technology_name(self.memory_technology)

    @property
    def operating_mode_names(self) -> tuple[str, ...]:
        return enums.memory_operating_mode_names(self.operating_mode_capability)


@dataclass(slots=True, frozen=True, kw_only=True)
class IPMIDevice:
    """SMBIOS Type 38 — IPMI Device Information."""

    handle: int
    interface_type: int
    spec_version_major: int
    spec_version_minor: int
    i2c_slave_address: int
    nv_storage_address: int
    base_address: int
    base_address_modifier: int
    interrupt_number: int

    @property
    def i2c_slave_address_canonical(self) -> int:
        """Canonical 7-bit BMC slave address. SMBIOS stores the byte with
        the I2C R/W bit pre-shifted in (so the raw byte == canonical << 1)."""
        return self.i2c_slave_address >> 1

    @property
    def base_address_value(self) -> int:
        """Base address with the address-space flag bit cleared. SMBIOS uses
        bit 0 of the qword to indicate the space type."""
        return self.base_address & ~0x01

    @property
    def base_address_io_mapped(self) -> bool:
        """True if the BMC interface is I/O port mapped (bit 0 of
        base_address); False if memory-mapped."""
        return bool(self.base_address & 0x01)


@dataclass(slots=True, frozen=True, kw_only=True)
class TPMDevice:
    """SMBIOS Type 43 — TPM Device."""

    handle: int
    vendor_id: str
    spec_major: int
    spec_minor: int
    firmware_version_1: int
    firmware_version_2: int
    description: str
    characteristics: int

    @property
    def firmware_version(self) -> str:
        """Decoded firmware revision in 'major.minor' form. Major is bits
        16-23 of firmware_version_1, minor is bits 0-7."""
        major = (self.firmware_version_1 >> 16) & 0xFF
        minor = self.firmware_version_1 & 0xFF
        return f"{major}.{minor}"


# SMBIOS Type 1 product-name prefixes burned in by production for each iX
# platform: z, x, m (incl. current minis), f, h, r, v, freenas-mini.
PLATFORM_PREFIXES: tuple[str, ...] = (
    "TRUENAS-Z",
    "TRUENAS-X",
    "TRUENAS-M",
    "TRUENAS-F",
    "TRUENAS-H",
    "TRUENAS-R",
    "TRUENAS-V",
    "FREENAS-MINI",
)

TRUENAS_UNKNOWN = "TRUENAS-UNKNOWN"


@dataclass(slots=True, frozen=True, kw_only=True)
class DMIInfo:
    """Aggregate of every SMBIOS structure parsed from one host in one pass.

    Singletons (``bios``, ``system``) are ``None`` when the corresponding
    SMBIOS type is absent. Lists are empty tuples when no structures of
    that type are present.
    """

    smbios_version: tuple[int, int]
    bios: BIOSInfo | None
    system: SystemInfo | None
    baseboards: tuple[BaseboardInfo, ...]
    chassis: tuple[ChassisInfo, ...]
    processors: tuple[ProcessorInfo, ...]
    caches: tuple[CacheInfo, ...]
    system_slots: tuple[SystemSlot, ...]
    oem_strings: tuple[str, ...]
    memory_arrays: tuple[MemoryArray, ...]
    memory_devices: tuple[MemoryDevice, ...]
    ipmi_devices: tuple[IPMIDevice, ...]
    tpm_devices: tuple[TPMDevice, ...]
    raw_structures: tuple[RawStructure, ...]
    tn_model: str

    @property
    def ecc_memory(self) -> bool:
        """True if any Physical Memory Array reports an ECC mode."""
        return any(enums.is_ecc(a.error_correction) for a in self.memory_arrays)

    @property
    def has_ipmi(self) -> bool:
        """True if any IPMI Device Information (Type 38) structure is present."""
        return bool(self.ipmi_devices)

    @property
    def has_tpm(self) -> bool:
        """True if any TPM Device (Type 43) structure is present."""
        return bool(self.tpm_devices)

    def cache_by_handle(self, handle: int) -> CacheInfo | None:
        """Look up a :class:`CacheInfo` by its SMBIOS structure handle.
        Useful for resolving the ``l1_cache_handle`` / ``l2_cache_handle`` /
        ``l3_cache_handle`` fields on :class:`ProcessorInfo`."""
        for c in self.caches:
            if c.handle == handle:
                return c
        return None
