import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Self

from core_domain.ddd import Entity, InvalidValue
from core_domain.ids import FileId

_SHA256 = re.compile(r"[0-9a-f]{64}")


class FileType(Enum):
    """Mirrors file.v1.FileType, without UNSPECIFIED, which is never valid."""

    GCODE = auto()
    CGCODE = auto()


@dataclass(eq=False)
class File(Entity[FileId]):
    """A file held in file storage. Its storage key is the domain's; where a store keeps the bytes
    under that key is infrastructure's concern."""

    id: FileId
    filename: str
    file_type: FileType
    size_bytes: int
    sha256: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls, filename: str, file_type: FileType, size_bytes: int, sha256: str, now: datetime
    ) -> Self:
        if not filename.strip():
            raise InvalidValue("A file must have a filename")
        if size_bytes <= 0:
            raise InvalidValue("A file must not be empty")
        if not _SHA256.fullmatch(sha256):
            raise InvalidValue("sha256 must be 64 lower-case hex characters")
        return cls(FileId.new(), filename, file_type, size_bytes, sha256, now, now)

    def storage_key(self) -> str:
        """Files with the same content share one stored copy under this key, so deleting a file
        removes its bytes only when no other file has the same key. The extension comes from the
        file's type, never from the uploader's filename."""
        return f"{self.sha256}.{self.file_type.name.lower()}"

    def check_content(self, size_bytes: int, sha256: str) -> None:
        """Rejects bytes that are not the ones this file was created to hold."""
        if size_bytes != self.size_bytes:
            raise InvalidValue(f"Expected {self.size_bytes} bytes, received {size_bytes}")
        if sha256 != self.sha256:
            raise InvalidValue("The file's content does not match its sha256")
