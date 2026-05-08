"""Pytest configuration and shared fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

_FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def dmi_fixture(monkeypatch):
    """Returns a callable that swaps ``TRUENAS_PYDMI_SYSFS_ROOT`` to point
    at a captured DMI fixture under ``tests/fixtures/dmi/<name>/`` and
    returns the ``truenas_pydmi`` module with caches cleared so the next
    call re-reads from the fixture root. The env var is reverted and the
    caches are cleared again on test teardown."""
    import truenas_pydmi as _dmi

    def _use(name: str):
        root = _FIXTURES_DIR / "dmi" / name
        if not (root / "sys/firmware/dmi/tables/DMI").exists():
            pytest.fail(f"DMI fixture not found: {root}")
        monkeypatch.setenv("TRUENAS_PYDMI_SYSFS_ROOT", str(root))
        _dmi.reload()
        return _dmi

    yield _use
    _dmi.reload()
