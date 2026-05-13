"""SMBIOS enumerated value name lookups.

These tables mirror the upstream dmidecode output strings verbatim
(see ``dmidecode/dmidecode.c`` in this repo). Keeping the names
byte-identical to what ``dmidecode`` prints means our output diffs
cleanly against it. Resync against upstream when bumping the
``dmidecode/`` submodule.

The dataclasses store the raw integers; callers that want a name call
the matching ``*_name()`` helper. This avoids the IntEnum/_missing_
dance for unknown values that real BIOSes inevitably emit.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType


def _lookup(table: Mapping[int, str], value: int) -> str:
    return table.get(value, f"Unknown(0x{value:02X})")


# Type 1 — Wake-up Type (dmi_system_wake_up_type)
_WAKE_UP_TYPES = MappingProxyType(
    {
        0x00: "Reserved",
        0x01: "Other",
        0x02: "Unknown",
        0x03: "APM Timer",
        0x04: "Modem Ring",
        0x05: "LAN Remote",
        0x06: "Power Switch",
        0x07: "PCI PME#",
        0x08: "AC Power Restored",
    }
)


def wake_up_type_name(value: int) -> str:
    return _lookup(_WAKE_UP_TYPES, value)


# Type 3 — Chassis Type (dmi_chassis_type; low 7 bits, bit 7 is the Lock bit)
_CHASSIS_TYPES = MappingProxyType(
    {
        0x01: "Other",
        0x02: "Unknown",
        0x03: "Desktop",
        0x04: "Low Profile Desktop",
        0x05: "Pizza Box",
        0x06: "Mini Tower",
        0x07: "Tower",
        0x08: "Portable",
        0x09: "Laptop",
        0x0A: "Notebook",
        0x0B: "Hand Held",
        0x0C: "Docking Station",
        0x0D: "All In One",
        0x0E: "Sub Notebook",
        0x0F: "Space-saving",
        0x10: "Lunch Box",
        0x11: "Main Server Chassis",
        0x12: "Expansion Chassis",
        0x13: "Sub Chassis",
        0x14: "Bus Expansion Chassis",
        0x15: "Peripheral Chassis",
        0x16: "RAID Chassis",
        0x17: "Rack Mount Chassis",
        0x18: "Sealed-case PC",
        0x19: "Multi-system",
        0x1A: "CompactPCI",
        0x1B: "AdvancedTCA",
        0x1C: "Blade",
        0x1D: "Blade Enclosing",
        0x1E: "Tablet",
        0x1F: "Convertible",
        0x20: "Detachable",
        0x21: "IoT Gateway",
        0x22: "Embedded PC",
        0x23: "Mini PC",
        0x24: "Stick PC",
    }
)


def chassis_type_name(value: int) -> str:
    return _lookup(_CHASSIS_TYPES, value & 0x7F)


# Type 4 — Processor Type (dmi_processor_type)
_PROCESSOR_TYPES = MappingProxyType(
    {
        0x01: "Other",
        0x02: "Unknown",
        0x03: "Central Processor",
        0x04: "Math Processor",
        0x05: "DSP Processor",
        0x06: "Video Processor",
    }
)


def processor_type_name(value: int) -> str:
    return _lookup(_PROCESSOR_TYPES, value)


# Type 4 — Processor Family (dmi_processor_family / family2[]).
#
# IMPORTANT: For *display* of the CPU, prefer ``ProcessorInfo.version`` —
# it's the marketing string the BIOS reports verbatim (e.g., "Intel(R)
# Xeon(R) D-2796NT CPU @ 2.00GHz") and is far more reliable than this
# table. Many BIOSes emit stale family codes for newer CPUs (e.g.,
# reporting 0xB2 / Pentium 4 for a modern Xeon D). This table is mainly
# useful for analytical/categorical use.
_PROCESSOR_FAMILIES = MappingProxyType(
    {
        0x01: "Other",
        0x02: "Unknown",
        0x03: "8086",
        0x04: "80286",
        0x05: "80386",
        0x06: "80486",
        0x07: "8087",
        0x08: "80287",
        0x09: "80387",
        0x0A: "80487",
        0x0B: "Pentium",
        0x0C: "Pentium Pro",
        0x0D: "Pentium II",
        0x0E: "Pentium MMX",
        0x0F: "Celeron",
        0x10: "Pentium II Xeon",
        0x11: "Pentium III",
        0x12: "M1",
        0x13: "M2",
        0x14: "Celeron M",
        0x15: "Pentium 4 HT",
        0x16: "Intel",
        0x18: "Duron",
        0x19: "K5",
        0x1A: "K6",
        0x1B: "K6-2",
        0x1C: "K6-3",
        0x1D: "Athlon",
        0x1E: "AMD29000",
        0x1F: "K6-2+",
        0x20: "Power PC",
        0x21: "Power PC 601",
        0x22: "Power PC 603",
        0x23: "Power PC 603+",
        0x24: "Power PC 604",
        0x25: "Power PC 620",
        0x26: "Power PC x704",
        0x27: "Power PC 750",
        0x28: "Core Duo",
        0x29: "Core Duo Mobile",
        0x2A: "Core Solo Mobile",
        0x2B: "Atom",
        0x2C: "Core M",
        0x2D: "Core m3",
        0x2E: "Core m5",
        0x2F: "Core m7",
        0x30: "Alpha",
        0x31: "Alpha 21064",
        0x32: "Alpha 21066",
        0x33: "Alpha 21164",
        0x34: "Alpha 21164PC",
        0x35: "Alpha 21164a",
        0x36: "Alpha 21264",
        0x37: "Alpha 21364",
        0x38: "Turion II Ultra Dual-Core Mobile M",
        0x39: "Turion II Dual-Core Mobile M",
        0x3A: "Athlon II Dual-Core M",
        0x3B: "Opteron 6100",
        0x3C: "Opteron 4100",
        0x3D: "Opteron 6200",
        0x3E: "Opteron 4200",
        0x3F: "FX",
        0x40: "MIPS",
        0x41: "MIPS R4000",
        0x42: "MIPS R4200",
        0x43: "MIPS R4400",
        0x44: "MIPS R4600",
        0x45: "MIPS R10000",
        0x46: "C-Series",
        0x47: "E-Series",
        0x48: "A-Series",
        0x49: "G-Series",
        0x4A: "Z-Series",
        0x4B: "R-Series",
        0x4C: "Opteron 4300",
        0x4D: "Opteron 6300",
        0x4E: "Opteron 3300",
        0x4F: "FirePro",
        0x50: "SPARC",
        0x51: "SuperSPARC",
        0x52: "MicroSPARC II",
        0x53: "MicroSPARC IIep",
        0x54: "UltraSPARC",
        0x55: "UltraSPARC II",
        0x56: "UltraSPARC IIi",
        0x57: "UltraSPARC III",
        0x58: "UltraSPARC IIIi",
        0x60: "68040",
        0x61: "68xxx",
        0x62: "68000",
        0x63: "68010",
        0x64: "68020",
        0x65: "68030",
        0x66: "Athlon X4",
        0x67: "Opteron X1000",
        0x68: "Opteron X2000",
        0x69: "Opteron A-Series",
        0x6A: "Opteron X3000",
        0x6B: "Zen",
        0x70: "Hobbit",
        0x78: "Crusoe TM5000",
        0x79: "Crusoe TM3000",
        0x7A: "Efficeon TM8000",
        0x80: "Weitek",
        0x82: "Itanium",
        0x83: "Athlon 64",
        0x84: "Opteron",
        0x85: "Sempron",
        0x86: "Turion 64",
        0x87: "Dual-Core Opteron",
        0x88: "Athlon 64 X2",
        0x89: "Turion 64 X2",
        0x8A: "Quad-Core Opteron",
        0x8B: "Third-Generation Opteron",
        0x8C: "Phenom FX",
        0x8D: "Phenom X4",
        0x8E: "Phenom X2",
        0x8F: "Athlon X2",
        0x90: "PA-RISC",
        0x91: "PA-RISC 8500",
        0x92: "PA-RISC 8000",
        0x93: "PA-RISC 7300LC",
        0x94: "PA-RISC 7200",
        0x95: "PA-RISC 7100LC",
        0x96: "PA-RISC 7100",
        0xA0: "V30",
        0xA1: "Quad-Core Xeon 3200",
        0xA2: "Dual-Core Xeon 3000",
        0xA3: "Quad-Core Xeon 5300",
        0xA4: "Dual-Core Xeon 5100",
        0xA5: "Dual-Core Xeon 5000",
        0xA6: "Dual-Core Xeon LV",
        0xA7: "Dual-Core Xeon ULV",
        0xA8: "Dual-Core Xeon 7100",
        0xA9: "Quad-Core Xeon 5400",
        0xAA: "Quad-Core Xeon",
        0xAB: "Dual-Core Xeon 5200",
        0xAC: "Dual-Core Xeon 7200",
        0xAD: "Quad-Core Xeon 7300",
        0xAE: "Quad-Core Xeon 7400",
        0xAF: "Multi-Core Xeon 7400",
        0xB0: "Pentium III Xeon",
        0xB1: "Pentium III Speedstep",
        0xB2: "Pentium 4",
        0xB3: "Xeon",
        0xB4: "AS400",
        0xB5: "Xeon MP",
        0xB6: "Athlon XP",
        0xB7: "Athlon MP",
        0xB8: "Itanium 2",
        0xB9: "Pentium M",
        0xBA: "Celeron D",
        0xBB: "Pentium D",
        0xBC: "Pentium EE",
        0xBD: "Core Solo",
        0xBF: "Core 2 Duo",
        0xC0: "Core 2 Solo",
        0xC1: "Core 2 Extreme",
        0xC2: "Core 2 Quad",
        0xC3: "Core 2 Extreme Mobile",
        0xC4: "Core 2 Duo Mobile",
        0xC5: "Core 2 Solo Mobile",
        0xC6: "Core i7",
        0xC7: "Dual-Core Celeron",
        0xC8: "IBM390",
        0xC9: "G4",
        0xCA: "G5",
        0xCB: "ESA/390 G6",
        0xCC: "z/Architecture",
        0xCD: "Core i5",
        0xCE: "Core i3",
        0xCF: "Core i9",
        0xD2: "C7-M",
        0xD3: "C7-D",
        0xD4: "C7",
        0xD5: "Eden",
        0xD6: "Multi-Core Xeon",
        0xD7: "Dual-Core Xeon 3xxx",
        0xD8: "Quad-Core Xeon 3xxx",
        0xD9: "Nano",
        0xDA: "Dual-Core Xeon 5xxx",
        0xDB: "Quad-Core Xeon 5xxx",
        0xDD: "Dual-Core Xeon 7xxx",
        0xDE: "Quad-Core Xeon 7xxx",
        0xDF: "Multi-Core Xeon 7xxx",
        0xE0: "Multi-Core Xeon 3400",
        0xE4: "Opteron 3000",
        0xE5: "Sempron II",
        0xE6: "Embedded Opteron Quad-Core",
        0xE7: "Phenom Triple-Core",
        0xE8: "Turion Ultra Dual-Core Mobile",
        0xE9: "Turion Dual-Core Mobile",
        0xEA: "Athlon Dual-Core",
        0xEB: "Sempron SI",
        0xEC: "Phenom II",
        0xED: "Athlon II",
        0xEE: "Six-Core Opteron",
        0xEF: "Sempron M",
        0xFA: "i860",
        0xFB: "i960",
        0x100: "ARMv7",
        0x101: "ARMv8",
        0x102: "ARMv9",
        0x103: "ARM",
        0x104: "SH-3",
        0x105: "SH-4",
        0x118: "ARM",
        0x119: "StrongARM",
        0x12C: "6x86",
        0x12D: "MediaGX",
        0x12E: "MII",
        0x140: "WinChip",
        0x15E: "DSP",
        0x1F4: "Video Processor",
        0x200: "RV32",
        0x201: "RV64",
        0x202: "RV128",
        0x258: "LoongArch",
        0x259: "Loongson 1",
        0x25A: "Loongson 2",
        0x25B: "Loongson 3",
        0x25C: "Loongson 2K",
        0x25D: "Loongson 3A",
        0x25E: "Loongson 3B",
        0x25F: "Loongson 3C",
        0x260: "Loongson 3D",
        0x261: "Loongson 3E",
        0x262: "Dual-Core Loongson 2K 2xxx",
        0x26C: "Quad-Core Loongson 3A 5xxx",
        0x26D: "Multi-Core Loongson 3A 5xxx",
        0x26E: "Quad-Core Loongson 3B 5xxx",
        0x26F: "Multi-Core Loongson 3B 5xxx",
        0x270: "Multi-Core Loongson 3C 5xxx",
        0x271: "Multi-Core Loongson 3D 5xxx",
    }
)


def processor_family_name(value: int) -> str:
    """Name for processor family. Handles both the legacy 1-byte field
    (Type 4 offset 6) and the 2-byte Family 2 field (offset 40+) used
    when the legacy field is 0xFE.

    Note: BIOSes routinely report stale or incorrect family codes for
    newer CPUs. Prefer ``ProcessorInfo.version`` for display.
    """
    return _lookup(_PROCESSOR_FAMILIES, value)


# Type 9 — Slot Type (dmi_slot_type)
_SLOT_TYPES = MappingProxyType(
    {
        0x01: "Other",
        0x02: "Unknown",
        0x03: "ISA",
        0x04: "MCA",
        0x05: "EISA",
        0x06: "PCI",
        0x07: "PC Card (PCMCIA)",
        0x08: "VLB",
        0x09: "Proprietary",
        0x0A: "Processor Card",
        0x0B: "Proprietary Memory Card",
        0x0C: "I/O Riser Card",
        0x0D: "NuBus",
        0x0E: "PCI-66",
        0x0F: "AGP",
        0x10: "AGP 2x",
        0x11: "AGP 4x",
        0x12: "PCI-X",
        0x13: "AGP 8x",
        0x14: "M.2 Socket 1-DP",
        0x15: "M.2 Socket 1-SD",
        0x16: "M.2 Socket 2",
        0x17: "M.2 Socket 3",
        0x18: "MXM Type I",
        0x19: "MXM Type II",
        0x1A: "MXM Type III",
        0x1B: "MXM Type III-HE",
        0x1C: "MXM Type IV",
        0x1D: "MXM 3.0 Type A",
        0x1E: "MXM 3.0 Type B",
        0x1F: "PCI Express 2 SFF-8639 (U.2)",
        0x20: "PCI Express 3 SFF-8639 (U.2)",
        0x21: "PCI Express Mini 52-pin with bottom-side keep-outs",
        0x22: "PCI Express Mini 52-pin without bottom-side keep-outs",
        0x23: "PCI Express Mini 76-pin",
        0x24: "PCI Express 4 SFF-8639 (U.2)",
        0x25: "PCI Express 5 SFF-8639 (U.2)",
        0x26: "OCP NIC 3.0 Small Form Factor (SFF)",
        0x27: "OCP NIC 3.0 Large Form Factor (LFF)",
        0x28: "OCP NIC Prior to 3.0",
        0x30: "CXL FLexbus 1.0",
        0xA0: "PC-98/C20",
        0xA1: "PC-98/C24",
        0xA2: "PC-98/E",
        0xA3: "PC-98/Local Bus",
        0xA4: "PC-98/Card",
        0xA5: "PCI Express",
        0xA6: "PCI Express x1",
        0xA7: "PCI Express x2",
        0xA8: "PCI Express x4",
        0xA9: "PCI Express x8",
        0xAA: "PCI Express x16",
        0xAB: "PCI Express 2",
        0xAC: "PCI Express 2 x1",
        0xAD: "PCI Express 2 x2",
        0xAE: "PCI Express 2 x4",
        0xAF: "PCI Express 2 x8",
        0xB0: "PCI Express 2 x16",
        0xB1: "PCI Express 3",
        0xB2: "PCI Express 3 x1",
        0xB3: "PCI Express 3 x2",
        0xB4: "PCI Express 3 x4",
        0xB5: "PCI Express 3 x8",
        0xB6: "PCI Express 3 x16",
        0xB8: "PCI Express 4",
        0xB9: "PCI Express 4 x1",
        0xBA: "PCI Express 4 x2",
        0xBB: "PCI Express 4 x4",
        0xBC: "PCI Express 4 x8",
        0xBD: "PCI Express 4 x16",
        0xBE: "PCI Express 5",
        0xBF: "PCI Express 5 x1",
        0xC0: "PCI Express 5 x2",
        0xC1: "PCI Express 5 x4",
        0xC2: "PCI Express 5 x8",
        0xC3: "PCI Express 5 x16",
        0xC4: "PCI Express 6+",
        0xC5: "EDSFF E1",
        0xC6: "EDSFF E3",
    }
)


def slot_type_name(value: int) -> str:
    return _lookup(_SLOT_TYPES, value)


# Type 9 — Slot Current Usage (dmi_slot_current_usage)
_SLOT_USAGE = MappingProxyType(
    {
        0x01: "Other",
        0x02: "Unknown",
        0x03: "Available",
        0x04: "In Use",
        0x05: "Unavailable",
    }
)


def slot_usage_name(value: int) -> str:
    return _lookup(_SLOT_USAGE, value)


# Type 9 — Slot Length (dmi_slot_length)
_SLOT_LENGTHS = MappingProxyType(
    {
        0x01: "Other",
        0x02: "Unknown",
        0x03: "Short",
        0x04: "Long",
        0x05: '2.5" drive form factor',
        0x06: '3.5" drive form factor',
    }
)


def slot_length_name(value: int) -> str:
    return _lookup(_SLOT_LENGTHS, value)


# Type 16 — Memory Error Correction (dmi_memory_array_ec_type)
_MEMORY_ERROR_CORRECTION = MappingProxyType(
    {
        0x01: "Other",
        0x02: "Unknown",
        0x03: "None",
        0x04: "Parity",
        0x05: "Single-bit ECC",
        0x06: "Multi-bit ECC",
        0x07: "CRC",
    }
)


def memory_error_correction_name(value: int) -> str:
    return _lookup(_MEMORY_ERROR_CORRECTION, value)


def is_ecc(memory_error_correction: int) -> bool:
    """True if the value indicates ECC of any kind (single-bit, multi-bit, CRC)."""
    return memory_error_correction in (0x05, 0x06, 0x07)


# Type 17 — Memory Form Factor (dmi_memory_device_form_factor)
_MEMORY_FORM_FACTORS = MappingProxyType(
    {
        0x01: "Other",
        0x02: "Unknown",
        0x03: "SIMM",
        0x04: "SIP",
        0x05: "Chip",
        0x06: "DIP",
        0x07: "ZIP",
        0x08: "Proprietary Card",
        0x09: "DIMM",
        0x0A: "TSOP",
        0x0B: "Row Of Chips",
        0x0C: "RIMM",
        0x0D: "SODIMM",
        0x0E: "SRIMM",
        0x0F: "FB-DIMM",
        0x10: "Die",
    }
)


def memory_form_factor_name(value: int) -> str:
    return _lookup(_MEMORY_FORM_FACTORS, value)


# Type 17 — Memory Type (dmi_memory_device_type)
_MEMORY_TYPES = MappingProxyType(
    {
        0x01: "Other",
        0x02: "Unknown",
        0x03: "DRAM",
        0x04: "EDRAM",
        0x05: "VRAM",
        0x06: "SRAM",
        0x07: "RAM",
        0x08: "ROM",
        0x09: "Flash",
        0x0A: "EEPROM",
        0x0B: "FEPROM",
        0x0C: "EPROM",
        0x0D: "CDRAM",
        0x0E: "3DRAM",
        0x0F: "SDRAM",
        0x10: "SGRAM",
        0x11: "RDRAM",
        0x12: "DDR",
        0x13: "DDR2",
        0x14: "DDR2 FB-DIMM",
        0x15: "Reserved",
        0x16: "Reserved",
        0x17: "Reserved",
        0x18: "DDR3",
        0x19: "FBD2",
        0x1A: "DDR4",
        0x1B: "LPDDR",
        0x1C: "LPDDR2",
        0x1D: "LPDDR3",
        0x1E: "LPDDR4",
        0x1F: "Logical non-volatile device",
        0x20: "HBM",
        0x21: "HBM2",
        0x22: "DDR5",
        0x23: "LPDDR5",
        0x24: "HBM3",
    }
)


def memory_type_name(value: int) -> str:
    return _lookup(_MEMORY_TYPES, value)


# Type 17 — Memory Type Detail (dmi_memory_device_type_detail; bitfield, bits 1-15)
_MEMORY_TYPE_DETAIL_BITS = MappingProxyType(
    {
        0x0002: "Other",
        0x0004: "Unknown",
        0x0008: "Fast-paged",
        0x0010: "Static Column",
        0x0020: "Pseudo-static",
        0x0040: "RAMBus",
        0x0080: "Synchronous",
        0x0100: "CMOS",
        0x0200: "EDO",
        0x0400: "Window DRAM",
        0x0800: "Cache DRAM",
        0x1000: "Non-Volatile",
        0x2000: "Registered (Buffered)",
        0x4000: "Unbuffered (Unregistered)",
        0x8000: "LRDIMM",
    }
)


def memory_type_detail_names(value: int) -> tuple[str, ...]:
    return tuple(name for bit, name in _MEMORY_TYPE_DETAIL_BITS.items() if value & bit)


# Type 17 — Memory Technology (dmi_memory_technology, SMBIOS 3.2+)
_MEMORY_TECHNOLOGIES = MappingProxyType(
    {
        0x01: "Other",
        0x02: "Unknown",
        0x03: "DRAM",
        0x04: "NVDIMM-N",
        0x05: "NVDIMM-F",
        0x06: "NVDIMM-P",
        0x07: "Intel Optane DC persistent memory",
    }
)


def memory_technology_name(value: int) -> str:
    return _lookup(_MEMORY_TECHNOLOGIES, value)


# Type 17 — Memory Operating Mode Capability (dmi_memory_operating_mode_capability;
# SMBIOS 3.2+, bitfield, bits 1-5)
_MEMORY_OPERATING_MODE_BITS = MappingProxyType(
    {
        0x0002: "Other",
        0x0004: "Unknown",
        0x0008: "Volatile memory",
        0x0010: "Byte-accessible persistent memory",
        0x0020: "Block-accessible persistent memory",
    }
)


def memory_operating_mode_names(value: int) -> tuple[str, ...]:
    return tuple(name for bit, name in _MEMORY_OPERATING_MODE_BITS.items() if value & bit)


# Type 0 — BIOS Characteristics qword (dmi_bios_characteristics; bits 3-31)
_BIOS_CHARACTERISTICS = MappingProxyType(
    {
        0x0000000000000008: "BIOS characteristics not supported",
        0x0000000000000010: "ISA is supported",
        0x0000000000000020: "MCA is supported",
        0x0000000000000040: "EISA is supported",
        0x0000000000000080: "PCI is supported",
        0x0000000000000100: "PC Card (PCMCIA) is supported",
        0x0000000000000200: "PNP is supported",
        0x0000000000000400: "APM is supported",
        0x0000000000000800: "BIOS is upgradeable",
        0x0000000000001000: "BIOS shadowing is allowed",
        0x0000000000002000: "VLB is supported",
        0x0000000000004000: "ESCD support is available",
        0x0000000000008000: "Boot from CD is supported",
        0x0000000000010000: "Selectable boot is supported",
        0x0000000000020000: "BIOS ROM is socketed",
        0x0000000000040000: "Boot from PC Card (PCMCIA) is supported",
        0x0000000000080000: "EDD is supported",
        0x0000000000100000: "Japanese floppy for NEC 9800 1.2 MB is supported (int 13h)",
        0x0000000000200000: "Japanese floppy for Toshiba 1.2 MB is supported (int 13h)",
        0x0000000000400000: '5.25"/360 kB floppy services are supported (int 13h)',
        0x0000000000800000: '5.25"/1.2 MB floppy services are supported (int 13h)',
        0x0000000001000000: '3.5"/720 kB floppy services are supported (int 13h)',
        0x0000000002000000: '3.5"/2.88 MB floppy services are supported (int 13h)',
        0x0000000004000000: "Print screen service is supported (int 5h)",
        0x0000000008000000: "8042 keyboard services are supported (int 9h)",
        0x0000000010000000: "Serial services are supported (int 14h)",
        0x0000000020000000: "Printer services are supported (int 17h)",
        0x0000000040000000: "CGA/mono video services are supported (int 10h)",
        0x0000000080000000: "NEC PC-98",
    }
)


# Type 0 — BIOS Characteristics Extension Byte 1 (dmi_bios_characteristics_x1)
_BIOS_CHAR_EXT_BYTE_1 = MappingProxyType(
    {
        0x01: "ACPI is supported",
        0x02: "USB legacy is supported",
        0x04: "AGP is supported",
        0x08: "I2O boot is supported",
        0x10: "LS-120 boot is supported",
        0x20: "ATAPI Zip drive boot is supported",
        0x40: "IEEE 1394 boot is supported",
        0x80: "Smart battery is supported",
    }
)


# Type 0 — BIOS Characteristics Extension Byte 2 (dmi_bios_characteristics_x2)
_BIOS_CHAR_EXT_BYTE_2 = MappingProxyType(
    {
        0x01: "BIOS boot specification is supported",
        0x02: "Function key-initiated network boot is supported",
        0x04: "Targeted content distribution is supported",
        0x08: "UEFI is supported",
        0x10: "System is a virtual machine",
        0x20: "Manufacturing mode is supported",
        0x40: "Manufacturing mode is enabled",
    }
)


# Type 7 — Cache Error Correction Type (dmi_cache_ec_type)
_CACHE_ERROR_CORRECTION = MappingProxyType(
    {
        0x01: "Other",
        0x02: "Unknown",
        0x03: "None",
        0x04: "Parity",
        0x05: "Single-bit ECC",
        0x06: "Multi-bit ECC",
    }
)


def cache_error_correction_name(value: int) -> str:
    return _lookup(_CACHE_ERROR_CORRECTION, value)


# Type 7 — System Cache Type (dmi_cache_type)
_CACHE_SYSTEM_TYPES = MappingProxyType(
    {
        0x01: "Other",
        0x02: "Unknown",
        0x03: "Instruction",
        0x04: "Data",
        0x05: "Unified",
    }
)


def cache_system_type_name(value: int) -> str:
    return _lookup(_CACHE_SYSTEM_TYPES, value)


# Type 7 — Cache Associativity (dmi_cache_associativity)
_CACHE_ASSOCIATIVITIES = MappingProxyType(
    {
        0x01: "Other",
        0x02: "Unknown",
        0x03: "Direct Mapped",
        0x04: "2-way Set-associative",
        0x05: "4-way Set-associative",
        0x06: "Fully Associative",
        0x07: "8-way Set-associative",
        0x08: "16-way Set-associative",
        0x09: "12-way Set-associative",
        0x0A: "24-way Set-associative",
        0x0B: "32-way Set-associative",
        0x0C: "48-way Set-associative",
        0x0D: "64-way Set-associative",
        0x0E: "20-way Set-associative",
    }
)


def cache_associativity_name(value: int) -> str:
    return _lookup(_CACHE_ASSOCIATIVITIES, value)


# Type 7 — SRAM Type (dmi_cache_types; bitfield)
_CACHE_SRAM_TYPE_BITS = MappingProxyType(
    {
        0x01: "Other",
        0x02: "Unknown",
        0x04: "Non-burst",
        0x08: "Burst",
        0x10: "Pipeline Burst",
        0x20: "Synchronous",
        0x40: "Asynchronous",
    }
)


def cache_sram_type_names(value: int) -> tuple[str, ...]:
    return tuple(name for bit, name in _CACHE_SRAM_TYPE_BITS.items() if value & bit)


# Type 7 — Cache Location (dmi_cache_location; extracted from Configuration bits 5-6).
# Upstream uses ``out_of_spec`` for value 0x02; we omit it so the lookup falls
# through to the generic "Unknown(0x02)" formatter.
_CACHE_LOCATIONS = MappingProxyType(
    {
        0x00: "Internal",
        0x01: "External",
        0x03: "Unknown",
    }
)


def cache_location_name(value: int) -> str:
    return _lookup(_CACHE_LOCATIONS, value)


# Type 7 — Cache Operational Mode (dmi_cache_mode; extracted from Configuration bits 8-9)
_CACHE_OPERATIONAL_MODES = MappingProxyType(
    {
        0x00: "Write Through",
        0x01: "Write Back",
        0x02: "Varies With Memory Address",
        0x03: "Unknown",
    }
)


def cache_operational_mode_name(value: int) -> str:
    return _lookup(_CACHE_OPERATIONAL_MODES, value)


def bios_characteristics_names(value: int, extension_bytes: bytes = b"") -> tuple[str, ...]:
    """Decode the 64-bit BIOS Characteristics bitfield plus the optional
    1- or 2-byte extension into a tuple of human-readable feature names.

    Names match upstream dmidecode verbatim. Note dmidecode short-circuits
    when bit 3 ('BIOS characteristics not supported') is set and skips the
    rest of the qword; we follow that convention but still surface the
    extension-byte features (which dmidecode also prints regardless)."""
    names: list[str] = []
    if value & 0x08:
        names.append("BIOS characteristics not supported")
    else:
        for bit, name in _BIOS_CHARACTERISTICS.items():
            if bit == 0x08:
                continue
            if value & bit:
                names.append(name)
    if len(extension_bytes) >= 1:
        for bit, name in _BIOS_CHAR_EXT_BYTE_1.items():
            if extension_bytes[0] & bit:
                names.append(name)
    if len(extension_bytes) >= 2:
        for bit, name in _BIOS_CHAR_EXT_BYTE_2.items():
            if extension_bytes[1] & bit:
                names.append(name)
    return tuple(names)


# Type 38 — IPMI Interface Type (dmi_ipmi_interface_type)
_IPMI_INTERFACE_TYPES = MappingProxyType(
    {
        0x00: "Unknown",
        0x01: "KCS (Keyboard Control Style)",
        0x02: "SMIC (Server Management Interface Chip)",
        0x03: "BT (Block Transfer)",
        0x04: "SSIF (SMBus System Interface)",
    }
)


def ipmi_interface_type_name(value: int) -> str:
    return _lookup(_IPMI_INTERFACE_TYPES, value)
