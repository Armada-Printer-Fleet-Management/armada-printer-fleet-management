from collections.abc import AsyncIterable, AsyncIterator
from datetime import UTC, datetime
from types import TracebackType
from typing import Self

import pytest
from core_domain.content_asset import File, FileType
from core_domain.ddd import EntityNotFound, Unavailable
from core_domain.ids import UserId
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


async def test_the_store_is_built_and_opened_only_when_the_adapter_is() -> None:
    events: list[str] = []
    files = files_over(events)
    assert events == []

    async def serve() -> None:
        async with files:
            assert events == ["built", "opened"]

    await serve()
    assert events == ["built", "opened", "closed"]


async def test_a_healthy_store_passes_its_check() -> None:
    events: list[str] = []

    async def check() -> None:
        async with files_over(events) as files:
            await files.health_check()

    await check()
    assert "checked" in events


async def test_a_store_outage_is_unavailable_without_its_details() -> None:
    async def check() -> None:
        async with files_over([], healthy=False) as files:
            await files.health_check()

    with pytest.raises(Unavailable) as raised:
        await check()

    assert str(raised.value) == "file storage is unavailable"
    assert isinstance(raised.value.__cause__, FileStoreError)


async def test_a_store_that_is_not_open_is_unavailable() -> None:
    with pytest.raises(Unavailable):
        await files_over([]).health_check()


async def test_bytes_missing_from_the_store_are_not_found_for_the_file() -> None:
    file = File.create(UserId.new(), "part.gcode", FileType.GCODE, 1, "a" * 64, datetime.now(UTC))

    async with FileStoreFiles(MemoryFileStore) as files:
        with pytest.raises(EntityNotFound) as raised:
            await files.read(file)

    assert raised.value.entity_id == file.id


@pytest.mark.parametrize("name", ["has_upload", "read", "delete"])
async def test_a_store_outage_is_unavailable_for_every_operation(name: str) -> None:
    file = File.create(UserId.new(), "part.gcode", FileType.GCODE, 1, "a" * 64, datetime.now(UTC))
    store = MemoryFileStore()

    async with FileStoreFiles(lambda: store) as files:
        store.healthy = False
        with pytest.raises(Unavailable):
            await getattr(files, name)(file)
