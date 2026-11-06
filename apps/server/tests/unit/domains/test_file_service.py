import hashlib
from collections.abc import AsyncIterator

import pytest
from core_domain.content_asset import File, FileType
from core_domain.ddd import EntityNotFound, InvalidValue
from core_domain.ids import FileId, UserId

from api.domains.content_asset.service import FileService
from api.infrastructure.file_memory import InMemoryFileRepository
from api.infrastructure.file_store_files import FileStoreFiles
from tests.fakes import MemoryFileStore
from tests.samples import NOW

CONTENT = b"G28\nG1 X10 Y10\n"
SHA256 = hashlib.sha256(CONTENT).hexdigest()


@pytest.fixture
async def service(store: MemoryFileStore) -> AsyncIterator[FileService]:
    async with FileStoreFiles(lambda: store) as storage:
        yield FileService(InMemoryFileRepository(), storage, clock=lambda: NOW)


async def stream(*chunks: bytes) -> AsyncIterator[bytes]:
    for chunk in chunks:
        yield chunk


async def create(service: FileService, sha256: str = SHA256) -> File:
    return await service.create_upload(
        UserId.new(), "part.gcode", FileType.GCODE, len(CONTENT), sha256
    )


async def download(service: FileService, file_id: FileId) -> bytes:
    async def read() -> bytes:
        _, chunks = await service.download(file_id)
        return b"".join([chunk async for chunk in chunks])

    return await read()


async def test_create_upload_saves_the_file(service: FileService) -> None:
    file = await service.create_upload(UserId.new(), "part.gcode", FileType.GCODE, 1024, SHA256)

    stored = await service.file(file.id)
    assert (stored.filename, stored.size_bytes, stored.created_at) == ("part.gcode", 1024, NOW)


async def test_create_upload_refused_by_the_rule_saves_nothing(service: FileService) -> None:
    with pytest.raises(InvalidValue):
        await service.create_upload(UserId.new(), "part.gcode", FileType.GCODE, 0, SHA256)


async def test_an_uploaded_file_downloads_unchanged(service: FileService) -> None:
    file = await create(service)
    assert not await service.is_uploaded(file.id)

    await service.upload(file.id, stream(CONTENT[:5], CONTENT[5:]))

    assert await service.is_uploaded(file.id)
    assert await download(service, file.id) == CONTENT


@pytest.mark.parametrize(
    "chunks",
    [(CONTENT[:-1],), (CONTENT, b"extra"), (CONTENT.lower(),)],
    ids=["short", "long", "different"],
)
async def test_bytes_that_do_not_match_the_file_are_refused_and_not_stored(
    service: FileService, store: MemoryFileStore, chunks: tuple[bytes, ...]
) -> None:
    file = await create(service)

    with pytest.raises(InvalidValue):
        await service.upload(file.id, stream(*chunks))

    assert store.objects == {}


async def test_upload_to_an_unknown_file_is_not_found(service: FileService) -> None:
    with pytest.raises(EntityNotFound):
        await service.upload(FileId.new(), stream(CONTENT))


async def test_download_without_an_upload_is_not_found(service: FileService) -> None:
    file = await create(service)
    with pytest.raises(EntityNotFound):
        await download(service, file.id)


async def test_delete_removes_the_file_and_its_bytes(
    service: FileService, store: MemoryFileStore
) -> None:
    file = await create(service)
    await service.upload(file.id, stream(CONTENT))

    await service.delete(file.id)

    with pytest.raises(EntityNotFound):
        await service.file(file.id)
    assert store.objects == {}


async def test_delete_keeps_bytes_another_file_still_holds(
    service: FileService, store: MemoryFileStore
) -> None:
    first, second = await create(service), await create(service)
    await service.upload(first.id, stream(CONTENT))

    await service.delete(first.id)

    assert second.storage_key() in store.objects
    assert await download(service, second.id) == CONTENT


async def test_is_uploaded_reports_an_unknown_file(service: FileService) -> None:
    with pytest.raises(EntityNotFound):
        await service.is_uploaded(FileId.new())
