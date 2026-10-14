from collections.abc import Iterable
from typing import Protocol

from core_domain.ddd import AsyncRepository
from core_domain.file import File
from core_domain.ids import FileId


class FileRepository(AsyncRepository[FileId, File], Protocol):
    """Where the server keeps file records. Implementations live in api/infrastructure, and each
    must pass tests/contract/test_file_repository.py. A save must not silently overwrite a
    change saved by another request since this one loaded the file."""

    async def get_many(self, file_ids: Iterable[FileId]) -> list[File]:
        """The files that exist among file_ids, in no particular order. Unknown IDs are skipped."""
        ...
