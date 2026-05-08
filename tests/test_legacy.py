"""Tests for the legacy ``ixhardware.parse_dmi()`` shim."""

from __future__ import annotations

import datetime


def test_h30_legacy_shim(dmi_fixture):
    """Drop-in replacement for ``ixhardware.parse_dmi()`` returns the same
    field set on a populated system."""
    dmi = dmi_fixture("h30_supermicro")
    info = dmi.legacy_dmi_info()
    assert info.bios_release_date == datetime.date(2025, 1, 6)
    assert info.ecc_memory is True
    assert info.baseboard_manufacturer == "Supermicro"
    assert info.baseboard_product_name == "X12SDV-20C-SPT8F"
    assert info.system_manufacturer == "iXsystems"
    assert info.system_product_name == "TRUENAS-H30-HA"
    assert info.system_serial_number == "A" * 9
    assert info.system_version == "1.0"
    assert info.has_ipmi is True


def test_qemu_legacy_shim_no_baseboard(dmi_fixture):
    """When Type 2 is absent (QEMU), baseboard fields fall back to empty
    strings rather than raising."""
    dmi = dmi_fixture("qemu_seabios")
    info = dmi.legacy_dmi_info()
    assert info.baseboard_manufacturer == ""
    assert info.baseboard_product_name == ""
    assert info.has_ipmi is False
    assert info.system_manufacturer == "QEMU"


def test_mini3x_legacy_shim_no_ipmi(dmi_fixture):
    dmi = dmi_fixture("mini3x_atom")
    info = dmi.legacy_dmi_info()
    assert info.has_ipmi is False
    assert info.system_product_name == "FREENAS-MINI-3.0-X"
