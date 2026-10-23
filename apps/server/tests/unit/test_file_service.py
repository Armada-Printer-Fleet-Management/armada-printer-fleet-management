import asyncio
import hashlib
from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
from core_domain.ddd import EntityNotFound, InvalidValue
from core_domain.file import File, FileType
from core_domain.ids import FileId

from api.domains.file.service import FileService
from api.infrastructure.file_memory import InMemoryFileRepository
from api.infrastructure.file_store_files import FileStoreFiles
from tests.fakes import MemoryFileStore

NOW = datetime(2026, 10, 7, 12, 0, tzinfo=UTC)
CONTENT = b"G28\nG1 X10 Y10\n"
SHA256 = hashlib.sha256(CONTENT).hexdigest()


@pytest.fixture
def store() -> MemoryFileStore:
    return MemoryFileStore()


@pytest.fixture
def service(store: MemoryFileStore) -> FileService:
    storage = FileStoreFiles(lambda: store)
    asyncio.run(storage.__aenter__())
    return FileService(InMemoryFileRepository(), storage, clock=lambda: NOW)


async def stream(*chunks: bytes) -> AsyncIterator[bytes]:
    for chunk in chunks:
        yield chunk


def create(service: FileService, sha256: str = SHA256) -> File:
    return asyncio.run(service.create_upload("part.gcode", FileType.GCODE, len(CONTENT), sha256))


def download(service: FileService, file_id: FileId) -> bytes:
    async def read() -> bytes:
        _, chunks = await service.download(file_id)
        return b"".join([chunk async for chunk in chunks])

    return asyncio.run(read())


def test_create_upload_saves_the_file(service: FileService) -> None:
    file = asyncio.run(service.create_upload("part.gcode", FileType.GCODE, 1024, SHA256))

    stored = asyncio.run(service.file(file.id))
    assert (stored.filename, stored.size_bytes, stored.created_at) == ("part.gcode", 1024, NOW)


def test_create_upload_refused_by_the_rule_saves_nothing(service: FileService) -> None:
    with pytest.raises(InvalidValue):
        asyncio.run(service.create_upload("part.gcode", FileType.GCODE, 0, SHA256))


def test_an_uploaded_file_downloads_unchanged(service: FileService) -> None:
    file = create(service)
    assert not asyncio.run(service.is_uploaded(file.id))

    asyncio.run(service.upload(file.id, stream(CONTENT[:5], CONTENT[5:])))

    assert asyncio.run(service.is_uploaded(file.id))
    assert download(service, file.id) == CONTENT


@pytest.mark.parametrize(
    "chunks",
    [(CONTENT[:-1],), (CONTENT, b"extra"), (CONTENT.lower(),)],
    ids=["short", "long", "different"],
)
def test_bytes_that_do_not_match_the_file_are_refused_and_not_stored(
    service: FileService, store: MemoryFileStore, chunks: tuple[bytes, ...]
) -> None:
    file = create(service)

    with pytest.raises(InvalidValue):
        asyncio.run(service.upload(file.id, stream(*chunks)))

    assert store.objects == {}


def test_upload_to_an_unknown_file_is_not_found(service: FileService) -> None:
    with pytest.raises(EntityNotFound):
        asyncio.run(service.upload(FileId.new(), stream(CONTENT)))


def test_download_without_an_upload_is_not_found(service: FileService) -> None:
    file = create(service)
    with pytest.raises(EntityNotFound):
        download(service, file.id)


def test_delete_removes_the_file_and_its_bytes(
    service: FileService, store: MemoryFileStore
) -> None:
    file = create(service)
    asyncio.run(service.upload(file.id, stream(CONTENT)))

    asyncio.run(service.delete(file.id))

    with pytest.raises(EntityNotFound):
        asyncio.run(service.file(file.id))
    assert store.objects == {}


def test_delete_keeps_bytes_another_file_still_holds(
    service: FileService, store: MemoryFileStore
) -> None:
    first, second = create(service), create(service)
    asyncio.run(service.upload(first.id, stream(CONTENT)))

    asyncio.run(service.delete(first.id))

    assert second.storage_key() in store.objects
    assert download(service, second.id) == CONTENT


def test_is_uploaded_reports_an_unknown_file(service: FileService) -> None:
    with pytest.raises(EntityNotFound):
        asyncio.run(service.is_uploaded(FileId.new()))
