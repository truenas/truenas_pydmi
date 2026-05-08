"""Sanitize captured SMBIOS DMI bytes so the fixtures can live in version control.

Replaces serial numbers, asset tags, and the System Information UUID with
same-length placeholders ('A' for strings, zero bytes for the UUID) so that
all structure boundaries remain byte-identical. The string-index fields in
the formatted areas are not touched — the strings they reference are
overwritten in place.

Usage::

    python3 tests/fixtures/dmi/_sanitize.py <input_DMI_bytes> <output_DMI_bytes>

Run once per captured fixture. The ``smbios_entry_point`` file does not need
sanitizing and is committed verbatim.
"""

from __future__ import annotations

from pathlib import Path
import struct
import sys

# (structure_type, offset_in_formatted_area_of_string_index): label
_SENSITIVE_STRING_FIELDS: dict[tuple[int, int], str] = {
    (1, 3): "system.serial_number",
    (2, 3): "baseboard.serial_number",
    (2, 4): "baseboard.asset_tag",
    (3, 3): "chassis.serial_number",
    (3, 4): "chassis.asset_tag",
    (4, 28): "processor.serial_number",
    (4, 29): "processor.asset_tag",
    (17, 20): "memory_device.serial_number",
    (17, 21): "memory_device.asset_tag",
}


def sanitize(data: bytes) -> tuple[bytes, list[str]]:
    """Return ``(sanitized_bytes, log)`` where ``log`` lists each replacement made."""
    out = bytearray(data)
    log: list[str] = []
    offset = 0

    while offset < len(out):
        if offset + 4 > len(out):
            break
        type_, length, _handle = struct.unpack_from("<BBH", out, offset)
        if length < 4:
            break
        formatted_end = offset + length
        if formatted_end > len(out):
            break

        # Type 1: zero out the 16-byte UUID at formatted offset 4 (file offset +8).
        if type_ == 1 and formatted_end >= offset + 24:
            for i in range(16):
                out[offset + 8 + i] = 0
            log.append(f"  type=1 uuid: zeroed at offset {offset + 8}")

        # Walk the string table to record (start, length) per 1-based string index.
        cursor = formatted_end
        string_spans: list[tuple[int, int]] = []
        if cursor + 1 < len(out) and out[cursor] == 0 and out[cursor + 1] == 0:
            cursor += 2  # no strings
        else:
            while cursor < len(out):
                nul = bytes(out).find(b"\x00", cursor)
                if nul < 0:
                    break
                string_spans.append((cursor, nul - cursor))
                cursor = nul + 1
                if cursor < len(out) and out[cursor] == 0:
                    cursor += 1
                    break

        # Replace sensitive strings with 'A' * len, preserving null terminators.
        for (st_type, fmt_off), label in _SENSITIVE_STRING_FIELDS.items():
            if st_type != type_:
                continue
            idx_byte = offset + 4 + fmt_off
            if idx_byte >= formatted_end:
                continue
            string_idx = out[idx_byte]
            if string_idx == 0 or string_idx > len(string_spans):
                continue
            start, slen = string_spans[string_idx - 1]
            if slen == 0:
                continue
            original = bytes(out[start : start + slen]).decode("latin-1", errors="replace")
            for i in range(slen):
                out[start + i] = ord("A")
            log.append(f"  type={st_type} {label}: {original!r} -> {'A' * slen!r}")

        offset = cursor
        if type_ == 127:
            break

    return bytes(out), log


def main(in_path: str, out_path: str) -> None:
    data = Path(in_path).read_bytes()
    sanitized, log = sanitize(data)
    Path(out_path).write_bytes(sanitized)
    print(f"sanitized {len(data)} -> {out_path}")
    for line in log:
        print(line)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    main(sys.argv[1], sys.argv[2])
