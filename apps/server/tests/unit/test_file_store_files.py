import asyncio
from collections.abc import AsyncIterable, AsyncIterator
from datetime import UTC, datetime
from types import TracebackType
from typing import Self

import pytest
from core_domain.ddd import EntityNotFound, Unavailable
from core_domain.file import File, FileType
from plugin_api.file_store import FileStoreError

from api.infrastructure.file_store_files import FileStoreFiles
from tests.fakes import MemoryFileStore


class RecordingFileStore:
    """A file store that records its lifetime, and fails health checks when told to."""

    def __init__(self, events: list[str], healthy: bool = True) -> None:
        self.events = events
        self.healthy = healthy

    async def __aenter__(self) -> Self:
        self.events.append("opened")
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.events.append("closed")

    async def read(self, key: str) -> AsyncIterator[bytes]:
        raise NotImplementedError

    async def write(self, key: str, chunks: AsyncIterable[bytes]) -> None:
        raise NotImplementedError

    async def exists(self, key: str) -> bool:
        raise NotImplementedError

    async def delete(self, key: str) -> None:
        raise NotImplementedError

    async def health_check(self) -> None:
        self.events.append("checked")
        if not self.healthy:
            raise FileStoreError("localhost:3900 refused the connection")


def files_over(events: list[str], healthy: bool = True) -> FileStoreFiles:
    def open_store() -> RecordingFileStore:
        events.append("built")
        return RecordingFileStore(events, healthy)

    return FileStoreFiles(open_store)


def test_the_store_is_built_and_opened_only_when_the_adapter_is() -> None:
    events: list[str] = []
    files = files_over(events)
    assert events == []

    async def serve() -> None:
        async with files:
            assert events == ["built", "opened"]

    asyncio.run(serve())
    assert events == ["built", "opened", "closed"]


def test_a_healthy_store_passes_its_check() -> None:
    events: list[str] = []

    async def check() -> None:
        async with files_over(events) as files:
            await files.health_check()

    asyncio.run(check())
    assert "checked" in events


def test_a_store_outage_is_unavailable_without_its_details() -> None:
    async def check() -> None:
        async with files_over([], healthy=False) as files:
            await files.health_check()

    with pytest.raises(Unavailable) as raised:
        asyncio.run(check())

    assert str(raised.value) == "file storage is unavailable"
    assert isinstance(raised.value.__cause__, FileStoreError)


def test_a_store_that_is_not_open_is_unavailable() -> None:
    with pytest.raises(Unavailable):
        asyncio.run(files_over([]).health_check())


def opened_over(store: MemoryFileStore) -> FileStoreFiles:
    files = FileStoreFiles(lambda: store)
    asyncio.run(files.__aenter__())
    return files


def test_bytes_missing_from_the_store_are_not_found_for_the_file() -> None:
    file = File.create("part.gcode", FileType.GCODE, 1, "a" * 64, datetime.now(UTC))

    with pytest.raises(EntityNotFound) as raised:
        asyncio.run(opened_over(MemoryFileStore()).read(file))

    assert raised.value.entity_id == file.id


@pytest.mark.parametrize("name", ["has_upload", "read", "delete"])
def test_a_store_outage_is_unavailable_for_every_operation(name: str) -> None:
    file = File.create("part.gcode", FileType.GCODE, 1, "a" * 64, datetime.now(UTC))
    store = MemoryFileStore()
    files = opened_over(store)
    store.healthy = False

    with pytest.raises(Unavailable):
        asyncio.run(getattr(files, name)(file))
