"""Pytest configuration and shared fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from truenas_pydmi.reader import read_dmi

_FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def dmi_fixture(monkeypatch):
    """Return a callable that points ``TRUENAS_PYDMI_SYSFS_ROOT`` at a
    captured DMI fixture under ``tests/fixtures/dmi/<name>/`` and returns
    a fresh :class:`truenas_pydmi.models.DMIInfo` parsed from it."""

    def _use(name: str):
        root = _FIXTURES_DIR / "dmi" / name
        if not (root / "sys/firmware/dmi/tables/DMI").exists():
            pytest.fail(f"DMI fixture not found: {root}")
        monkeypatch.setenv("TRUENAS_PYDMI_SYSFS_ROOT", str(root))
        return read_dmi()

    return _use
