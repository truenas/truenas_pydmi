"""Public API for the dmi subsystem.

Reads SMBIOS / DMI tables from ``/sys/firmware/dmi/tables/`` and exposes
typed accessors. Replaces the legacy ``ixhardware.parse_dmi()`` (which
shells out to ``dmidecode``) and ``middlewared/plugins/system/dmi.py``.
"""

from __future__ import annotations

import functools

from . import parser, structures
from ._enums import (
    bios_characteristics_names,
    cache_associativity_name,
    cache_error_correction_name,
    cache_location_name,
    cache_operational_mode_name,
    cache_sram_type_names,
    cache_system_type_name,
    chassis_type_name,
    ipmi_interface_type_name,
    is_ecc,
    memory_error_correction_name,
    memory_form_factor_name,
    memory_operating_mode_names,
    memory_technology_name,
    memory_type_detail_names,
    memory_type_name,
    processor_family_name,
    processor_type_name,
    slot_length_name,
    slot_type_name,
    slot_usage_name,
    wake_up_type_name,
)
from ._legacy import LegacyDMIInfo, legacy_dmi_info
from .errors import (
    DMIError,
    DMIPermissionError,
    DMIProtocolError,
    DMIUnavailableError,
)
from .models import (
    BaseboardInfo,
    BIOSInfo,
    CacheInfo,
    ChassisInfo,
    IPMIDevice,
    MemoryArray,
    MemoryDevice,
    ProcessorInfo,
    RawStructure,
    SystemInfo,
    SystemSlot,
    TPMDevice,
)


def is_available() -> bool:
    """True if SMBIOS tables are present on this system."""
    return parser.is_available()


@functools.cache
def smbios_version() -> tuple[int, int]:
    """``(major, minor)`` from the SMBIOS entry-point structure."""
    ep = parser.parse_dmi().entry_point
    return (ep.major, ep.minor)


@functools.cache
def bios() -> BIOSInfo:
    """SMBIOS Type 0. Raises :class:`DMIError` if not present."""
    for raw in parser.parse_dmi().structures:
        if raw.type == 0:
            return structures.parse_bios(raw)
    raise DMIError("no Type 0 (BIOS Information) structure found")


@functools.cache
def system() -> SystemInfo:
    """SMBIOS Type 1. Raises :class:`DMIError` if not present."""
    for raw in parser.parse_dmi().structures:
        if raw.type == 1:
            return structures.parse_system(raw)
    raise DMIError("no Type 1 (System Information) structure found")


@functools.cache
def baseboards() -> tuple[BaseboardInfo, ...]:
    """SMBIOS Type 2. May be empty (rare) or have multiple entries."""
    return tuple(structures.parse_baseboard(r) for r in parser.parse_dmi().structures if r.type == 2)


@functools.cache
def chassis() -> tuple[ChassisInfo, ...]:
    """SMBIOS Type 3."""
    return tuple(structures.parse_chassis(r) for r in parser.parse_dmi().structures if r.type == 3)


@functools.cache
def processors() -> tuple[ProcessorInfo, ...]:
    """SMBIOS Type 4. One entry per CPU socket; check ``.populated`` to
    distinguish populated sockets from empty ones."""
    return tuple(structures.parse_processor(r) for r in parser.parse_dmi().structures if r.type == 4)


@functools.cache
def caches() -> tuple[CacheInfo, ...]:
    """SMBIOS Type 7 — Cache Information. Typically one entry per cache
    level (L1, L2, L3) per CPU socket."""
    return tuple(structures.parse_cache(r) for r in parser.parse_dmi().structures if r.type == 7)


def cache(handle: int) -> CacheInfo | None:
    """Look up a cache by SMBIOS structure handle. Useful for resolving
    the ``l1_cache_handle`` / ``l2_cache_handle`` / ``l3_cache_handle``
    fields on :class:`ProcessorInfo`. Returns ``None`` if no cache with
    that handle exists."""
    for c in caches():
        if c.handle == handle:
            return c
    return None


@functools.cache
def system_slots() -> tuple[SystemSlot, ...]:
    """SMBIOS Type 9 — physical expansion slots (PCIe, M.2, etc.)."""
    return tuple(structures.parse_system_slot(r) for r in parser.parse_dmi().structures if r.type == 9)


@functools.cache
def oem_strings() -> tuple[str, ...]:
    """SMBIOS Type 11 — flat list across all Type 11 structures."""
    out: list[str] = []
    for r in parser.parse_dmi().structures:
        if r.type == 11:
            out.extend(structures.parse_oem_strings(r))
    return tuple(out)


@functools.cache
def memory_arrays() -> tuple[MemoryArray, ...]:
    """SMBIOS Type 16."""
    return tuple(structures.parse_memory_array(r) for r in parser.parse_dmi().structures if r.type == 16)


@functools.cache
def memory_devices() -> tuple[MemoryDevice, ...]:
    """SMBIOS Type 17 — one entry per DIMM slot, populated or not."""
    return tuple(structures.parse_memory_device(r) for r in parser.parse_dmi().structures if r.type == 17)


@functools.cache
def ipmi_devices() -> tuple[IPMIDevice, ...]:
    """SMBIOS Type 38."""
    return tuple(structures.parse_ipmi_device(r) for r in parser.parse_dmi().structures if r.type == 38)


@functools.cache
def tpm_devices() -> tuple[TPMDevice, ...]:
    """SMBIOS Type 43."""
    return tuple(structures.parse_tpm_device(r) for r in parser.parse_dmi().structures if r.type == 43)


@functools.cache
def ecc_memory() -> bool:
    """True if any Physical Memory Array reports an ECC mode."""
    return any(is_ecc(a.error_correction) for a in memory_arrays())


@functools.cache
def has_ipmi() -> bool:
    """True if any IPMI Device Information (Type 38) structure is present."""
    return bool(ipmi_devices())


@functools.cache
def has_tpm() -> bool:
    """True if any TPM Device (Type 43) structure is present."""
    return bool(tpm_devices())


@functools.cache
def raw_structures() -> tuple[RawStructure, ...]:
    """All structures as parsed by the structure-stream walker, including
    types we don't have typed accessors for."""
    return parser.parse_dmi().structures


_CACHED_FUNCTIONS = (
    parser.parse_dmi,
    parser.is_available,
    smbios_version,
    bios,
    system,
    baseboards,
    chassis,
    processors,
    caches,
    system_slots,
    oem_strings,
    memory_arrays,
    memory_devices,
    ipmi_devices,
    tpm_devices,
    ecc_memory,
    has_ipmi,
    has_tpm,
    raw_structures,
    legacy_dmi_info,
)


def reload() -> None:
    """Drop every cached parse and accessor result. For tests and the rare
    runtime case of hot-pluggable management hardware."""
    for fn in _CACHED_FUNCTIONS:
        fn.cache_clear()


__all__ = [
    # exceptions
    "DMIError",
    "DMIUnavailableError",
    "DMIPermissionError",
    "DMIProtocolError",
    # availability
    "is_available",
    # singletons
    "smbios_version",
    "bios",
    "system",
    # lists
    "baseboards",
    "chassis",
    "processors",
    "caches",
    "system_slots",
    "oem_strings",
    "memory_arrays",
    "memory_devices",
    "ipmi_devices",
    "tpm_devices",
    # by-handle lookups
    "cache",
    # predicates
    "ecc_memory",
    "has_ipmi",
    "has_tpm",
    # escape hatches
    "raw_structures",
    # cache control
    "reload",
    # legacy migration
    "LegacyDMIInfo",
    "legacy_dmi_info",
    # name helpers
    "bios_characteristics_names",
    "cache_associativity_name",
    "cache_error_correction_name",
    "cache_location_name",
    "cache_operational_mode_name",
    "cache_sram_type_names",
    "cache_system_type_name",
    "chassis_type_name",
    "ipmi_interface_type_name",
    "is_ecc",
    "memory_error_correction_name",
    "memory_form_factor_name",
    "memory_operating_mode_names",
    "memory_technology_name",
    "memory_type_detail_names",
    "memory_type_name",
    "processor_family_name",
    "processor_type_name",
    "slot_length_name",
    "slot_type_name",
    "slot_usage_name",
    "wake_up_type_name",
    # dataclasses
    "BIOSInfo",
    "BaseboardInfo",
    "CacheInfo",
    "ChassisInfo",
    "IPMIDevice",
    "MemoryArray",
    "MemoryDevice",
    "ProcessorInfo",
    "RawStructure",
    "SystemInfo",
    "SystemSlot",
    "TPMDevice",
]
