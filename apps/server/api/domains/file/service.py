from collections.abc import Callable, Iterable
from datetime import datetime

from core_domain.ddd import Service
from core_domain.file import File, FileType
from core_domain.ids import FileId

from api.domains.file.repository import FileRepository
from api.domains.file.storage import FileStorage


class FileService(Service[FileRepository]):
    def __init__(
        self, repository: FileRepository, storage: FileStorage, clock: Callable[[], datetime]
    ) -> None:
        super().__init__(repository)
        self._storage = storage
        self._clock = clock

    async def file(self, file_id: FileId) -> File:
        return await self._repository.get(file_id)

    async def files(self, file_ids: Iterable[FileId]) -> list[File]:
        return await self._repository.get_many(file_ids)

    async def create_upload(
        self, filename: str, file_type: FileType, size_bytes: int, sha256: str
    ) -> tuple[File, str]:
        """Records a file about to be uploaded, and returns it with where to PUT its bytes."""
        file = File.create(filename, file_type, size_bytes, sha256, self._clock())
        await self._repository.save(file)
        return file, self._storage.upload_url(file.id)

    async def is_uploaded(self, file_id: FileId) -> bool:
        return await self._storage.has_upload(await self._repository.get(file_id))
