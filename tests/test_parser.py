"""Tests for the SMBIOS entry-point parser and structure-stream walker."""

from __future__ import annotations

import pytest

from truenas_pydmi.errors import DMIUnavailableError
from truenas_pydmi.private import parser
from truenas_pydmi.reader import read_dmi


@pytest.mark.parametrize(
    "fixture,expected_version",
    [
        ("h30_supermicro", (3, 5)),
        ("f60_viking", (3, 3)),
        ("m50_supermicro_x11", (3, 2)),
        ("mini3x_atom", (3, 0)),
        ("qemu_seabios", (2, 8)),
    ],
)
def test_smbios_version(dmi_fixture, fixture, expected_version):
    dmi = dmi_fixture(fixture)
    assert dmi.smbios_version == expected_version


@pytest.mark.parametrize(
    "fixture,expected_count",
    [
        ("h30_supermicro", 60),
        ("f60_viking", 73),
        ("m50_supermicro_x11", 83),
        ("mini3x_atom", 20),
        ("qemu_seabios", 13),
    ],
)
def test_total_structure_count(dmi_fixture, fixture, expected_count):
    dmi = dmi_fixture(fixture)
    assert len(dmi.raw_structures) == expected_count


def test_is_available(dmi_fixture):
    dmi_fixture("h30_supermicro")
    assert parser.is_available() is True


def test_unavailable_when_root_missing(monkeypatch, tmp_path):
    """When the sysfs root points at a directory with no DMI tables,
    ``parser.is_available()`` is False and :func:`read` raises."""
    monkeypatch.setenv("TRUENAS_PYDMI_SYSFS_ROOT", str(tmp_path))
    assert parser.is_available() is False
    with pytest.raises(DMIUnavailableError):
        read_dmi()


def test_end_of_table_terminator(dmi_fixture):
    """The walker should stop at Type 127 (End-of-Table); no fixture should
    have a Type 127 followed by anything else parseable."""
    dmi = dmi_fixture("h30_supermicro")
    end_of_table = [s for s in dmi.raw_structures if s.type == 127]
    assert len(end_of_table) == 1
    assert dmi.raw_structures[-1].type == 127


def test_string_table_terminator(dmi_fixture):
    """Every parsed structure should have a string tuple — possibly empty,
    but always terminated by the walker (we'd raise DMIProtocolError otherwise)."""
    dmi = dmi_fixture("qemu_seabios")
    for s in dmi.raw_structures:
        assert isinstance(s.strings, tuple)
