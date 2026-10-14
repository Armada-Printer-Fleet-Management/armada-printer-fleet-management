"""What every FileRepository must do, whatever stores the records. A new adapter joins by adding
its factory to ADAPTERS."""

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime

import pytest
from core_domain.ddd import EntityNotFound
from core_domain.file import File, FileType
from core_domain.ids import FileId

from api.domains.file.repository import FileRepository
from api.infrastructure.file_memory import InMemoryFileRepository

ADAPTERS: list[Callable[[], FileRepository]] = [InMemoryFileRepository]
NOW = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)


@pytest.fixture(params=ADAPTERS, ids=lambda factory: factory.__name__)
def repository(request: pytest.FixtureRequest) -> FileRepository:
    factory: Callable[[], FileRepository] = request.param
    return factory()


def file() -> File:
    return File.create("part.gcode", FileType.GCODE, 1024, "c" * 64, NOW)


def test_get_reports_an_unknown_id(repository: FileRepository) -> None:
    with pytest.raises(EntityNotFound):
        asyncio.run(repository.get(FileId.new()))


def test_save_then_get_round_trips_every_field(repository: FileRepository) -> None:
    stored = file()
    asyncio.run(repository.save(stored))
    assert vars(asyncio.run(repository.get(stored.id))) == vars(stored)


def test_a_change_is_stored_only_once_saved(repository: FileRepository) -> None:
    stored = file()
    asyncio.run(repository.save(stored))

    asyncio.run(repository.get(stored.id)).filename = "changed.gcode"

    assert asyncio.run(repository.get(stored.id)).filename == "part.gcode"


def test_get_many_returns_the_known_files_and_skips_the_rest(repository: FileRepository) -> None:
    first, second = file(), file()
    for stored in (first, second):
        asyncio.run(repository.save(stored))

    found = asyncio.run(repository.get_many([first.id, FileId.new(), second.id, first.id]))

    assert {stored.id for stored in found} == {first.id, second.id}
    assert len(found) == 2
