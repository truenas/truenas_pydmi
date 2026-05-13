"""Entry point: build a populated :class:`DMIInfo` from the live SMBIOS tables."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from truenas_pydmi import models
from truenas_pydmi.private import parser, structures

T = TypeVar("T")


def read_dmi() -> models.DMIInfo:
    """Read and parse the SMBIOS tables and return an aggregate :class:`DMIInfo`.

    Performs all I/O and decoding in a single pass. Each call re-reads
    from sysfs — the result is intended to be held by the caller for as
    long as it's useful, not re-fetched per access.
    """
    parsed = parser.parse_dmi()
    raws = parsed.structures

    system = _first(raws, 1, structures.parse_system)
    baseboards = _all(raws, 2, structures.parse_baseboard)

    oem: list[str] = []
    for r in raws:
        if r.type == 11:
            oem.extend(structures.parse_oem_strings(r))

    return models.DMIInfo(
        smbios_version=(parsed.entry_point.major, parsed.entry_point.minor),
        bios=_first(raws, 0, structures.parse_bios),
        system=system,
        baseboards=baseboards,
        chassis=_all(raws, 3, structures.parse_chassis),
        processors=_all(raws, 4, structures.parse_processor),
        caches=_all(raws, 7, structures.parse_cache),
        system_slots=_all(raws, 9, structures.parse_system_slot),
        oem_strings=tuple(oem),
        memory_arrays=_all(raws, 16, structures.parse_memory_array),
        memory_devices=_all(raws, 17, structures.parse_memory_device),
        ipmi_devices=_all(raws, 38, structures.parse_ipmi_device),
        tpm_devices=_all(raws, 43, structures.parse_tpm_device),
        raw_structures=raws,
        tn_model=_tn_model(system, baseboards),
    )


def _first(raws: tuple[models.RawStructure, ...], type_id: int, fn: Callable[[models.RawStructure], T]) -> T | None:
    for r in raws:
        if r.type == type_id:
            return fn(r)
    return None


def _all(raws: tuple[models.RawStructure, ...], type_id: int, fn: Callable[[models.RawStructure], T]) -> tuple[T, ...]:
    return tuple(fn(r) for r in raws if r.type == type_id)


def _tn_model(system: models.SystemInfo | None, baseboards: tuple[models.BaseboardInfo, ...]) -> str:
    """Derive the TrueNAS platform model from Type 1 / Type 2 strings.

    Returns the SMBIOS Type 1 product name when it matches a known iX
    platform prefix. Falls back to ``"TRUENAS-X"`` on X10 systems where
    the model string was not burned into Type 1 but the baseboard product
    name identifies it. Returns ``models.TRUENAS_UNKNOWN`` otherwise.
    """
    if system and system.product_name.startswith(models.PLATFORM_PREFIXES):
        return system.product_name
    if baseboards and baseboards[0].product == "iXsystems TrueNAS X10":
        return "TRUENAS-X"
    return models.TRUENAS_UNKNOWN
