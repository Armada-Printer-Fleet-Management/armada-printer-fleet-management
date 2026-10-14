from typing import Protocol

from core_domain.file import File
from core_domain.ids import FileId


class FileStorage(Protocol):
    """Where file bytes live, apart from the database. Implementations are in api/infrastructure."""

    def upload_url(self, file_id: FileId) -> str:
        """Where the client PUTs the file's bytes. An opaque, short-lived credential."""
        ...

    async def has_upload(self, file: File) -> bool:
        """Whether the file's bytes have finished uploading and match its metadata."""
        ...
