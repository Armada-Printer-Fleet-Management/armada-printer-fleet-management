from abc import abstractmethod
from collections.abc import Iterable

from core_domain.ddd import AbstractAsyncRepository
from core_domain.file import File
from core_domain.ids import FileId


class FileRepository(AbstractAsyncRepository[FileId, File]):
    """Where the server keeps file records. Implementations live in api/infrastructure, and each
    must pass tests/contract/test_file_repository.py. A save must not silently overwrite a
    change saved by another request since this one loaded the file."""

    @abstractmethod
    async def get_many(self, file_ids: Iterable[FileId]) -> list[File]:
        """The files that exist among file_ids, in no particular order. Unknown IDs are skipped."""

    @abstractmethod
    async def delete(self, file_id: FileId) -> None:
        """Raises EntityNotFound if there is no such file."""

    @abstractmethod
    async def is_storage_key_used(self, storage_key: str) -> bool:
        """Whether any file's bytes are stored under this key, which decides whether they are
        still needed."""
