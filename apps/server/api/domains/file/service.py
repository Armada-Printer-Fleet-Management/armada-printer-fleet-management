import hashlib
from collections.abc import AsyncIterable, AsyncIterator, Callable, Iterable
from datetime import datetime

from core_domain.ddd import InvalidValue, Service
from core_domain.file import File, FileType
from core_domain.ids import FileId, UserId

from api.domains.file.repository import FileRepository
from api.domains.file.storage import FileStorage


async def _verified(file: File, chunks: AsyncIterable[bytes]) -> AsyncIterator[bytes]:
    """Passes the chunks on while checking them against the file, failing as soon as there are
    too many so an oversized upload is not read to the end."""
    digest = hashlib.sha256()
    size_bytes = 0
    async for chunk in chunks:
        size_bytes += len(chunk)
        if size_bytes > file.size_bytes:
            raise InvalidValue(f"Expected {file.size_bytes} bytes, received more instead")
        digest.update(chunk)
        yield chunk
    file.check_content(size_bytes, digest.hexdigest())


class FileService(Service[FileRepository]):
    def __init__(
        self,
        repository: FileRepository,
        storage: FileStorage,
        clock: Callable[[], datetime],
    ) -> None:
        super().__init__(repository)
        self._storage = storage
        self._clock = clock

    async def file(self, file_id: FileId) -> File:
        return await self._repository.get(file_id)

    async def files(self, file_ids: Iterable[FileId]) -> list[File]:
        return await self._repository.get_many(file_ids)

    async def create_upload(
        self, user_id: UserId, filename: str, file_type: FileType, size_bytes: int, sha256: str
    ) -> File:
        """Records a file about to be uploaded, before its bytes arrive."""
        file = File.create(user_id, filename, file_type, size_bytes, sha256, self._clock())
        await self._repository.save(file)
        return file

    async def is_uploaded(self, file_id: FileId) -> bool:
        return await self._storage.has_upload(await self._repository.get(file_id))

    async def upload(self, file_id: FileId, chunks: AsyncIterable[bytes]) -> None:
        """Stores the file's bytes. Raises InvalidValue, storing nothing, if they are not the bytes
        the file was created with."""
        file = await self._repository.get(file_id)
        await self._storage.write(file, _verified(file, chunks))

    async def download(self, file_id: FileId) -> tuple[File, AsyncIterator[bytes]]:
        file = await self._repository.get(file_id)
        return file, await self._storage.read(file)

    async def delete(self, file_id: FileId) -> None:
        """Deletes the file, and its bytes unless another file holds the same content. The record
        goes first, so a failure can orphan bytes but never leave a file without them."""
        file = await self._repository.get(file_id)
        await self._repository.delete(file_id)
        if not await self._repository.is_storage_key_used(file.storage_key()):
            await self._storage.delete(file)
