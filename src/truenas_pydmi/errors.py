class DMIError(Exception):
    """Base exception for everything raised by ``truenas_pydmi``."""


class DMIUnavailableError(DMIError):
    """SMBIOS tables are not present on this system (e.g. some ARM SBCs)."""

    def __init__(self, *paths: str) -> None:
        super().__init__("DMI tables not available at: " + ", ".join(paths))
        self.paths = paths


class DMIPermissionError(DMIError):
    """Read access to /sys/firmware/dmi/tables/ was denied."""

    def __init__(self, path: str, cause: BaseException) -> None:
        super().__init__(f"permission denied reading {path}: {cause}")
        self.path = path
        self.__cause__ = cause


class DMIProtocolError(DMIError):
    """The SMBIOS entry point or structure stream is malformed."""

    def __init__(self, message: str, *, offset: int = -1) -> None:
        if offset >= 0:
            super().__init__(f"{message} (at byte offset {offset})")
        else:
            super().__init__(message)
        self.offset = offset
