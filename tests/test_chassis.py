"""Tests for the ``tn_model`` field on :class:`DMIInfo`."""

from __future__ import annotations

import pytest


@pytest.mark.parametrize(
    "fixture, expected",
    [
        ("h30_supermicro", "TRUENAS-H30-HA"),
        ("m50_supermicro_x11", "TRUENAS-M50-HA"),
        ("f60_viking", "TRUENAS-F60-HA"),
        ("mini3x_atom", "FREENAS-MINI-3.0-X"),
    ],
)
def test_known_platform_prefix(dmi_fixture, fixture, expected):
    """Type 1 product name with an iX platform prefix flows through verbatim."""
    dmi = dmi_fixture(fixture)
    assert dmi.tn_model == expected


def test_non_truenas_returns_unknown(dmi_fixture):
    """A non-iX host (QEMU) with no recognizable Type 1 prefix and no
    Type 2 baseboard resolves to the unknown sentinel rather than raising."""
    dmi = dmi_fixture("qemu_seabios")
    assert dmi.tn_model == "TRUENAS-UNKNOWN"
