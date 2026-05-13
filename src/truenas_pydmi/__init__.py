"""DMI / SMBIOS introspection for TrueNAS.

Entry point: :func:`truenas_pydmi.reader.read_dmi`. See the submodules:

- ``truenas_pydmi.reader`` — :func:`read_dmi` returns a populated :class:`DMIInfo`.
- ``truenas_pydmi.models`` — typed dataclasses including :class:`DMIInfo` and
  the per-structure types (:class:`BIOSInfo`, :class:`SystemInfo`, ...) plus
  :data:`PLATFORM_PREFIXES` and :data:`TRUENAS_UNKNOWN`.
- ``truenas_pydmi.enums`` — enum-name decoders for raw SMBIOS integer fields.
- ``truenas_pydmi.errors`` — exception hierarchy.
"""
