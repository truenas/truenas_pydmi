"""Compatibility shim that produces a dataclass matching the legacy
``ixhardware.DMIInfo`` shape, so middleware callers can switch over without
changing the field set they consume."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import functools


@dataclass(slots=True, frozen=True, kw_only=True)
class LegacyDMIInfo:
    bios_release_date: date | None = None
    ecc_memory: bool = False
    baseboard_manufacturer: str = ""
    baseboard_product_name: str = ""
    system_manufacturer: str = ""
    system_product_name: str = ""
    system_serial_number: str = ""
    system_version: str = ""
    has_ipmi: bool = False


@functools.cache
def legacy_dmi_info() -> LegacyDMIInfo:
    """Drop-in replacement for ``ixhardware.parse_dmi()``."""
    from . import (
        baseboards,
        bios,
        ecc_memory,
        has_ipmi,
        system,
    )

    bios_info = bios()
    sys_info = system()
    bbs = baseboards()
    bb = bbs[0] if bbs else None

    return LegacyDMIInfo(
        bios_release_date=bios_info.release_date,
        ecc_memory=ecc_memory(),
        baseboard_manufacturer=bb.manufacturer if bb else "",
        baseboard_product_name=bb.product if bb else "",
        system_manufacturer=sys_info.manufacturer,
        system_product_name=sys_info.product_name,
        system_serial_number=sys_info.serial_number,
        system_version=sys_info.version,
        has_ipmi=has_ipmi(),
    )
