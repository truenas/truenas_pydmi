"""SMBIOS entry-point parsing and structure-stream walking.

Reads ``/sys/firmware/dmi/tables/smbios_entry_point`` and
``/sys/firmware/dmi/tables/DMI`` and produces a tuple of
:class:`RawStructure` records.

Tests can override the sysfs root by setting the
``TRUENAS_PYDMI_SYSFS_ROOT`` environment variable.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import struct

from truenas_pydmi.errors import DMIPermissionError, DMIProtocolError, DMIUnavailableError
from truenas_pydmi.models import RawStructure

ENTRY_POINT_REL_PATH = "/sys/firmware/dmi/tables/smbios_entry_point"
TABLES_REL_PATH = "/sys/firmware/dmi/tables/DMI"


def _sysfs_root() -> str:
    return os.environ.get("TRUENAS_PYDMI_SYSFS_ROOT", "")


def _entry_point_path() -> str:
    return _sysfs_root() + ENTRY_POINT_REL_PATH


def _tables_path() -> str:
    return _sysfs_root() + TABLES_REL_PATH


@dataclass(slots=True, frozen=True, kw_only=True)
class EntryPoint:
    """Parsed SMBIOS entry-point structure (either 2.x ``_SM_`` or 3.x ``_SM3_``)."""

    major: int
    minor: int
    revision: int
    table_length: int


@dataclass(slots=True, frozen=True, kw_only=True)
class ParsedSMBIOS:
    """Result of one full SMBIOS read + parse pass."""

    entry_point: EntryPoint
    structures: tuple[RawStructure, ...]


def is_available() -> bool:
    return Path(_entry_point_path()).exists() and Path(_tables_path()).exists()


def _parse_entry_point(buf: bytes) -> EntryPoint:
    if len(buf) < 5:
        raise DMIProtocolError("entry point too short", offset=0)

    if buf[:5] == b"_SM3_":
        if len(buf) < 24:
            raise DMIProtocolError("SMBIOS 3 entry point too short", offset=0)
        major = buf[7]
        minor = buf[8]
        revision = buf[10]
        max_size = struct.unpack_from("<I", buf, 12)[0]
        return EntryPoint(major=major, minor=minor, revision=revision, table_length=max_size)

    if buf[:4] == b"_SM_":
        if len(buf) < 31:
            raise DMIProtocolError("SMBIOS 2 entry point too short", offset=0)
        major = buf[6]
        minor = buf[7]
        revision = buf[10]
        if buf[16:21] != b"_DMI_":
            raise DMIProtocolError("missing _DMI_ intermediate anchor", offset=16)
        table_length = struct.unpack_from("<H", buf, 22)[0]
        return EntryPoint(major=major, minor=minor, revision=revision, table_length=table_length)

    raise DMIProtocolError(f"unknown entry point anchor: {buf[:5]!r}", offset=0)


def _walk_structures(buf: bytes, max_length: int) -> tuple[RawStructure, ...]:
    structures: list[RawStructure] = []
    offset = 0
    end = min(len(buf), max_length) if max_length > 0 else len(buf)

    while offset < end:
        if offset + 4 > end:
            raise DMIProtocolError("truncated structure header", offset=offset)

        type_, length, handle = struct.unpack_from("<BBH", buf, offset)

        if length < 4:
            raise DMIProtocolError(f"structure length {length} < 4", offset=offset)

        formatted_end = offset + length
        if formatted_end > end:
            raise DMIProtocolError("formatted area extends past table end", offset=offset)

        formatted = bytes(buf[offset + 4 : formatted_end])

        # Walk the string table looking for the double-null terminator.
        cursor = formatted_end
        strings: list[str] = []

        # Special case: if the byte right after the formatted area is a null
        # AND the next is also null, there are no strings — consume both nulls.
        if cursor + 1 < len(buf) and buf[cursor] == 0 and buf[cursor + 1] == 0:
            cursor += 2
        else:
            terminated = False
            while cursor < len(buf):
                nul = buf.find(b"\x00", cursor)
                if nul < 0:
                    raise DMIProtocolError("string table not terminated", offset=cursor)
                strings.append(bytes(buf[cursor:nul]).decode("latin-1", errors="replace").strip())
                cursor = nul + 1
                if cursor < len(buf) and buf[cursor] == 0:
                    cursor += 1  # consume second null
                    terminated = True
                    break
            if not terminated:
                raise DMIProtocolError("string table not terminated (eof)", offset=cursor)

        structures.append(
            RawStructure(
                type=type_,
                handle=handle,
                formatted=formatted,
                strings=tuple(strings),
            )
        )

        offset = cursor

        if type_ == 127:  # End-of-Table
            break

    return tuple(structures)


def parse_dmi() -> ParsedSMBIOS:
    """Read and parse the SMBIOS tables fresh."""
    if not is_available():
        raise DMIUnavailableError(_entry_point_path(), _tables_path())

    ep_path = _entry_point_path()
    tbl_path = _tables_path()

    try:
        with open(ep_path, "rb") as f:
            ep_bytes = f.read()
    except PermissionError as e:
        raise DMIPermissionError(ep_path, e) from e

    try:
        with open(tbl_path, "rb") as f:
            table_bytes = f.read()
    except PermissionError as e:
        raise DMIPermissionError(tbl_path, e) from e

    entry_point = _parse_entry_point(ep_bytes)
    structures = _walk_structures(table_bytes, entry_point.table_length)
    return ParsedSMBIOS(entry_point=entry_point, structures=structures)
