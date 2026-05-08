# truenas_pydmi

Pure-Python DMI / SMBIOS introspection for TrueNAS. Reads
`/sys/firmware/dmi/tables/` directly and exposes typed dataclasses for
every SMBIOS structure type middleware cares about: BIOS, System,
Baseboard, Chassis, Processor, Cache, System Slots, OEM Strings, Memory
Array, Memory Device, IPMI Device, and TPM Device.

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
import truenas_pydmi as dmi

if not dmi.is_available():
    raise SystemExit("no SMBIOS tables on this system")

print(dmi.smbios_version())          # (3, 5)

b = dmi.bios()
print(b.vendor, b.version, b.release_date, b.rom_size_bytes)
for feature in b.characteristics_decoded:
    print(" -", feature)

s = dmi.system()
print(s.manufacturer, s.product_name, s.serial_number, s.uuid)

for d in dmi.memory_devices():
    if d.populated:
        print(d.locator, d.size_bytes, d.manufacturer, d.part_number)

for p in dmi.processors():
    l1 = dmi.cache(p.l1_cache_handle)
    print(p.version, p.voltage_volts, l1.installed_size_bytes if l1 else None)

print(dmi.ecc_memory(), dmi.has_ipmi(), dmi.has_tpm())
```

Every public accessor is `@functools.cache`'d, so repeated calls are
free. Call `dmi.reload()` to drop every cache (needed only for tests or
the rare case of hot-pluggable management hardware).

## Public API

| Function                  | Returns                              | Notes                                              |
| ------------------------- | ------------------------------------ | -------------------------------------------------- |
| `is_available()`          | `bool`                               | True if SMBIOS tables exist on this system         |
| `smbios_version()`        | `tuple[int, int]`                    | `(major, minor)` from the entry-point structure    |
| `bios()`                  | `BIOSInfo`                           | Type 0                                             |
| `system()`                | `SystemInfo`                         | Type 1                                             |
| `baseboards()`            | `tuple[BaseboardInfo, ...]`          | Type 2                                             |
| `chassis()`               | `tuple[ChassisInfo, ...]`            | Type 3                                             |
| `processors()`            | `tuple[ProcessorInfo, ...]`          | Type 4 (one per socket)                            |
| `caches()`                | `tuple[CacheInfo, ...]`              | Type 7                                             |
| `cache(handle)`           | `CacheInfo \| None`                  | Resolve `ProcessorInfo.l{1,2,3}_cache_handle`      |
| `system_slots()`          | `tuple[SystemSlot, ...]`             | Type 9                                             |
| `oem_strings()`           | `tuple[str, ...]`                    | Type 11 (flat across all entries)                  |
| `memory_arrays()`         | `tuple[MemoryArray, ...]`            | Type 16                                            |
| `memory_devices()`        | `tuple[MemoryDevice, ...]`           | Type 17 (one per DIMM slot, populated or not)      |
| `ipmi_devices()`          | `tuple[IPMIDevice, ...]`             | Type 38                                            |
| `tpm_devices()`           | `tuple[TPMDevice, ...]`              | Type 43                                            |
| `ecc_memory()`            | `bool`                               | True if any memory array reports ECC               |
| `has_ipmi()` / `has_tpm()`| `bool`                               | Convenience predicates                             |
| `raw_structures()`        | `tuple[RawStructure, ...]`           | Escape hatch for unparsed structure types          |
| `legacy_dmi_info()`       | `LegacyDMIInfo`                      | Drop-in shape for `ixhardware.DMIInfo`             |
| `reload()`                | `None`                               | Drop every cached parse and accessor result        |

Decoder helpers are exposed for the SMBIOS enum/bitfield values:
`bios_characteristics_names`, `chassis_type_name`,
`processor_family_name`, `memory_type_name`, `memory_form_factor_name`,
`memory_type_detail_names`, `memory_technology_name`,
`memory_operating_mode_names`, `memory_error_correction_name` /
`is_ecc`, `ipmi_interface_type_name`, `cache_associativity_name`,
`cache_error_correction_name`, `cache_location_name`,
`cache_operational_mode_name`, `cache_sram_type_names`,
`cache_system_type_name`, `slot_type_name`, `slot_usage_name`,
`slot_length_name`, `wake_up_type_name`.

The dataclasses also expose property decoders for fields that ship as
raw bitfields or encoded values (e.g. `ProcessorInfo.voltage_volts`,
`IPMIDevice.base_address_value` / `base_address_io_mapped`,
`TPMDevice.firmware_version`, `BIOSInfo.characteristics_decoded`,
`MemoryDevice.memory_technology_name`).

## Legacy compatibility

`legacy_dmi_info()` returns a dataclass with the same field set as the
older `ixhardware.DMIInfo`, suitable as a drop-in:

```python
from truenas_pydmi import legacy_dmi_info as parse_dmi

info = parse_dmi()
print(info.system_product_name, info.system_serial_number, info.has_ipmi)
```

## Errors

```
DMIError                              (Exception)
├── DMIUnavailableError               # no SMBIOS tables on this system
├── DMIPermissionError                # sysfs read denied
└── DMIProtocolError                  # entry point or structure malformed
```

`DMIUnavailableError` is the typical cause when running on a board with
no SMBIOS exposed (some ARM SBCs). Callers that care can guard with
`is_available()` first.

## Tests

```sh
pytest                               # captured-fixture tests; no sudo needed
ruff check src tests
ruff format --check src tests
```

Tests run against sanitized real-hardware DMI byte captures under
`tests/fixtures/dmi/<machine>/`. The `dmi_fixture` pytest fixture in
`tests/conftest.py` swaps `TRUENAS_PYDMI_SYSFS_ROOT` to point at one of
those captures and clears the parser cache.

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
