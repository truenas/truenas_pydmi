# truenas_pydmi

Pure-Python DMI / SMBIOS introspection for TrueNAS. Reads
`/sys/firmware/dmi/tables/` directly and exposes typed dataclasses for
every SMBIOS structure type middleware cares about: BIOS, System,
Baseboard, Chassis, Processor, Cache, System Slots, OEM Strings, Memory
Array, Memory Device, IPMI Device, and TPM Device. One entry point —
`read_dmi()` — returns a single populated `DMIInfo` dataclass.

## Requirements

- Linux
- Python 3.13+
- Read access to `/sys/firmware/dmi/tables/` — these files are mode
  `0400` root on most distros, so callers typically run as root or with
  `cap_dac_read_search`.

## Install

```sh
pip install -e .          # editable
pip install -e .[test]    # with pytest
```

## Usage

```python
from truenas_pydmi.reader import read_dmi

dmi = read_dmi()

print(dmi.smbios_version)            # (3, 5)
print(dmi.tn_model)                  # "TRUENAS-H30-HA", "TRUENAS-UNKNOWN", ...

b = dmi.bios
print(b.vendor, b.version, b.release_date, b.rom_size_bytes)
for feature in b.characteristics_decoded:
    print(" -", feature)

s = dmi.system
print(s.manufacturer, s.product_name, s.serial_number, s.uuid)

for d in dmi.memory_devices:
    if d.populated:
        print(d.locator, d.size_bytes, d.manufacturer, d.part_number)

for p in dmi.processors:
    l1 = dmi.cache_by_handle(p.l1_cache_handle)
    print(p.version, p.voltage_volts, l1.installed_size_bytes if l1 else None)

print(dmi.ecc_memory, dmi.has_ipmi, dmi.has_tpm)
```

`read_dmi()` parses the SMBIOS tables fresh on every call. There is no
internal caching — call it once, hold the returned `DMIInfo` for as long
as the result is useful. SMBIOS data is static within a process lifetime
so a single read at startup is the typical pattern.

## Layout

```
truenas_pydmi/
├── reader.py     read_dmi() -> DMIInfo
├── models.py     DMIInfo + per-type dataclasses + PLATFORM_PREFIXES / TRUENAS_UNKNOWN
├── enums.py      name decoders for SMBIOS integer fields
├── errors.py     exception hierarchy
└── private/      implementation details (do not import from here)
```

Callers always import from the public submodules:

```python
from truenas_pydmi.reader import read_dmi
from truenas_pydmi.models import DMIInfo, PLATFORM_PREFIXES, TRUENAS_UNKNOWN
from truenas_pydmi.enums  import chassis_type_name, processor_family_name
from truenas_pydmi.errors import DMIError, DMIUnavailableError
```

## DMIInfo

`read_dmi()` returns a frozen `DMIInfo` with these fields:

| Field             | Type                              | Notes                                                          |
| ----------------- | --------------------------------- | -------------------------------------------------------------- |
| `smbios_version`  | `tuple[int, int]`                 | `(major, minor)` from the entry-point structure                |
| `bios`            | `BIOSInfo \| None`                | Type 0                                                         |
| `system`          | `SystemInfo \| None`              | Type 1                                                         |
| `baseboards`      | `tuple[BaseboardInfo, ...]`       | Type 2                                                         |
| `chassis`         | `tuple[ChassisInfo, ...]`         | Type 3                                                         |
| `processors`      | `tuple[ProcessorInfo, ...]`       | Type 4 (one per socket)                                        |
| `caches`          | `tuple[CacheInfo, ...]`           | Type 7                                                         |
| `system_slots`    | `tuple[SystemSlot, ...]`          | Type 9                                                         |
| `oem_strings`     | `tuple[str, ...]`                 | Type 11 (flat across all entries)                              |
| `memory_arrays`   | `tuple[MemoryArray, ...]`         | Type 16                                                        |
| `memory_devices`  | `tuple[MemoryDevice, ...]`        | Type 17 (one per DIMM slot, populated or not)                  |
| `ipmi_devices`    | `tuple[IPMIDevice, ...]`          | Type 38                                                        |
| `tpm_devices`     | `tuple[TPMDevice, ...]`           | Type 43                                                        |
| `raw_structures`  | `tuple[RawStructure, ...]`        | Escape hatch for structure types without a typed parser        |
| `tn_model`        | `str`                             | TrueNAS platform identifier (`"TRUENAS-H30-HA"`, `"TRUENAS-UNKNOWN"`, …) |

Derived properties:

| Property                    | Returns                  | Notes                                                       |
| --------------------------- | ------------------------ | ----------------------------------------------------------- |
| `ecc_memory`                | `bool`                   | True if any memory array reports ECC                        |
| `has_ipmi` / `has_tpm`      | `bool`                   | Convenience predicates                                      |
| `cache_by_handle(handle)`   | `CacheInfo \| None`      | Resolve `ProcessorInfo.l{1,2,3}_cache_handle`               |

The per-type dataclasses also expose property decoders for fields that
ship as raw bitfields or encoded values (e.g. `ProcessorInfo.voltage_volts`,
`IPMIDevice.base_address_value` / `base_address_io_mapped`,
`TPMDevice.firmware_version`, `BIOSInfo.characteristics_decoded`,
`MemoryDevice.memory_technology_name`).

For enum/bitfield values not surfaced by a property, the helpers in
`truenas_pydmi.enums` provide the decoder:
`bios_characteristics_names`, `chassis_type_name`, `processor_family_name`,
`memory_type_name`, `memory_form_factor_name`, `memory_type_detail_names`,
`memory_technology_name`, `memory_operating_mode_names`,
`memory_error_correction_name` / `is_ecc`, `ipmi_interface_type_name`,
`cache_associativity_name`, `cache_error_correction_name`,
`cache_location_name`, `cache_operational_mode_name`,
`cache_sram_type_names`, `cache_system_type_name`, `slot_type_name`,
`slot_usage_name`, `slot_length_name`, `wake_up_type_name`.

## TrueNAS platform identification

`dmi.tn_model` is derived from the SMBIOS Type 1 product name. It
returns the product name verbatim when it starts with a known iX
platform prefix (see `models.PLATFORM_PREFIXES`), falls back to
`"TRUENAS-X"` on X10 systems where the model string was not burned into
Type 1 but the baseboard product name identifies it, and is
`models.TRUENAS_UNKNOWN` (`"TRUENAS-UNKNOWN"`) on everything else.

## Errors

```
DMIError                              (Exception)
├── DMIUnavailableError               # no SMBIOS tables on this system
├── DMIPermissionError                # sysfs read denied
└── DMIProtocolError                  # entry point or structure malformed
```

`read_dmi()` raises `DMIUnavailableError` on hosts with no exposed
SMBIOS (some ARM SBCs). Catch it at the call site if your code needs to
run on such hardware.

## Tests

```sh
pytest                               # captured-fixture tests; no sudo needed
ruff check src tests
ruff format --check src tests
```

Tests run against sanitized real-hardware DMI byte captures under
`tests/fixtures/dmi/<machine>/`. The `dmi_fixture` pytest fixture in
`tests/conftest.py` points `TRUENAS_PYDMI_SYSFS_ROOT` at one of those
captures and returns a freshly-parsed `DMIInfo`.

To capture a fixture from a new machine:

```sh
ssh root@host 'cat /sys/firmware/dmi/tables/smbios_entry_point' \
    > tests/fixtures/dmi/<name>/sys/firmware/dmi/tables/smbios_entry_point
ssh root@host 'cat /sys/firmware/dmi/tables/DMI' > /tmp/raw_DMI
python3 tests/fixtures/dmi/_sanitize.py /tmp/raw_DMI \
    tests/fixtures/dmi/<name>/sys/firmware/dmi/tables/DMI
```

The sanitizer replaces serial numbers, asset tags, and the System UUID
with same-length placeholders so the structure boundaries stay valid.
