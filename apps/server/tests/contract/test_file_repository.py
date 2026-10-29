"""What every FileRepository must do, whatever stores the records. A new adapter joins by adding
its factory to ADAPTERS. A factory is given the test's request, so one that needs a database can
ask for the postgres_database fixture and only its own tests need Postgres."""

from collections.abc import Callable
from datetime import UTC, datetime

import pytest
from core_domain.ddd import EntityNotFound
from core_domain.file import File, FileType
from core_domain.ids import FileId, UserId

from api.domains.file.repository import FileRepository
from api.infrastructure.file_memory import InMemoryFileRepository
from api.infrastructure.file_sql import SqlFileRepository
from api.infrastructure.postgres_database import PostgresDatabase
from tests.postgres import needs_postgres, run

type Factory = Callable[[pytest.FixtureRequest], FileRepository]


def _memory(request: pytest.FixtureRequest) -> FileRepository:
    return InMemoryFileRepository()


def _sql(request: pytest.FixtureRequest) -> FileRepository:
    database: PostgresDatabase = request.getfixturevalue("postgres_database")
    return SqlFileRepository(database)


ADAPTERS = [
    pytest.param(_memory, id="memory"),
    pytest.param(_sql, id="sql", marks=needs_postgres),
]
NOW = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)


@pytest.fixture(params=ADAPTERS)
def repository(request: pytest.FixtureRequest) -> FileRepository:
    factory: Factory = request.param
    return factory(request)


def file() -> File:
    return File.create(UserId.new(), "part.gcode", FileType.GCODE, 1024, "c" * 64, NOW)


def test_get_reports_an_unknown_id(repository: FileRepository) -> None:
    with pytest.raises(EntityNotFound):
        run(repository.get(FileId.new()))


def test_save_then_get_round_trips_every_field(repository: FileRepository) -> None:
    stored = file()
    run(repository.save(stored))
    assert vars(run(repository.get(stored.id))) == vars(stored)


def test_a_change_is_stored_only_once_saved(repository: FileRepository) -> None:
    stored = file()
    run(repository.save(stored))

    run(repository.get(stored.id)).filename = "changed.gcode"

    assert run(repository.get(stored.id)).filename == "part.gcode"


def test_get_many_returns_the_known_files_and_skips_the_rest(repository: FileRepository) -> None:
    first, second = file(), file()
    for stored in (first, second):
        run(repository.save(stored))

    found = run(repository.get_many([first.id, FileId.new(), second.id, first.id]))

    assert {stored.id for stored in found} == {first.id, second.id}
    assert len(found) == 2


def test_delete_removes_the_file(repository: FileRepository) -> None:
    stored = file()
    run(repository.save(stored))

    run(repository.delete(stored.id))

    with pytest.raises(EntityNotFound):
        run(repository.get(stored.id))


def test_delete_reports_an_unknown_id(repository: FileRepository) -> None:
    with pytest.raises(EntityNotFound):
        run(repository.delete(FileId.new()))


def test_is_storage_key_used_matches_a_stored_files_key(repository: FileRepository) -> None:
    stored = file()
    run(repository.save(stored))
    other_type = File.create(UserId.new(), "part.bgcode", FileType.CGCODE, 1024, stored.sha256, NOW)
    other_content = File.create(UserId.new(), "part.gcode", FileType.GCODE, 1024, "f" * 64, NOW)

    assert run(repository.is_storage_key_used(stored.storage_key()))
    assert not run(repository.is_storage_key_used(other_type.storage_key()))
    assert not run(repository.is_storage_key_used(other_content.storage_key()))
