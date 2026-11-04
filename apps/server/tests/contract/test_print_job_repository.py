"""What every PrintJobRepository must do, whatever stores the jobs. A new adapter joins by adding
its factory to ADAPTERS. A factory is given the test's request, so one that needs a database can
ask for the postgres_database fixture and only its own tests need Postgres."""

import base64
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from core_domain.ddd import EntityNotFound, InvalidPageToken
from core_domain.ids import PrintJobId, UserId
from core_domain.print_job import PrintJob, PrintJobStatus

from api.domains.print_job.repository import PrintJobRepository
from api.infrastructure.postgres_database import PostgresDatabase
from api.infrastructure.print_job_memory import InMemoryPrintJobRepository
from api.infrastructure.print_job_sql import SqlPrintJobRepository
from tests.postgres import needs_postgres, run

type Factory = Callable[[pytest.FixtureRequest], PrintJobRepository]


def _memory(request: pytest.FixtureRequest) -> PrintJobRepository:
    return InMemoryPrintJobRepository()


def _sql(request: pytest.FixtureRequest) -> PrintJobRepository:
    database: PostgresDatabase = request.getfixturevalue("postgres_database")
    return SqlPrintJobRepository(database)


ADAPTERS = [
    pytest.param(_memory, id="memory"),
    pytest.param(_sql, id="sql", marks=needs_postgres),
]
START = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)


@pytest.fixture(params=ADAPTERS)
def repository(request: pytest.FixtureRequest) -> PrintJobRepository:
    factory: Factory = request.param
    return factory(request)


def job(minutes: int = 0) -> PrintJob:
    time = START + timedelta(minutes=minutes)
    return PrintJob(PrintJobId.new(), UserId.new(), PrintJobStatus.DRAFT, time, time, "notes")


def saved(repository: PrintJobRepository, count: int) -> list[PrintJob]:
    jobs = [job(minutes) for minutes in range(count)]
    for print_job in jobs:
        run(repository.save(print_job))
    return jobs


def test_get_reports_an_unknown_id(repository: PrintJobRepository) -> None:
    with pytest.raises(EntityNotFound):
        run(repository.get(PrintJobId.new()))


def test_save_then_get_round_trips_every_field(repository: PrintJobRepository) -> None:
    print_job = job()
    run(repository.save(print_job))
    assert vars(run(repository.get(print_job.id))) == vars(print_job)


def test_a_change_is_stored_only_once_saved(repository: PrintJobRepository) -> None:
    print_job = job()
    run(repository.save(print_job))

    loaded = run(repository.get(print_job.id))
    loaded.user_notes = "changed"
    assert run(repository.get(print_job.id)).user_notes == "notes"

    run(repository.save(loaded))
    assert run(repository.get(print_job.id)).user_notes == "changed"


def test_page_returns_newest_first_and_ends_with_an_empty_token(
    repository: PrintJobRepository,
) -> None:
    jobs = saved(repository, 5)

    first = run(repository.page(2, ""))
    second = run(repository.page(2, first.next_page_token))
    last = run(repository.page(2, second.next_page_token))

    paged = [print_job.id for page in (first, second, last) for print_job in page.items]
    assert paged == [print_job.id for print_job in reversed(jobs)]
    assert first.next_page_token and second.next_page_token
    assert last.next_page_token == ""


def test_a_page_that_holds_the_rest_has_no_next_token(repository: PrintJobRepository) -> None:
    saved(repository, 2)
    page = run(repository.page(2, ""))
    assert len(page.items) == 2
    assert page.next_page_token == ""


def test_page_of_an_empty_repository(repository: PrintJobRepository) -> None:
    page = run(repository.page(10, ""))
    assert (page.items, page.next_page_token) == ([], "")


@pytest.mark.parametrize(
    "token",
    [
        "not a token",
        "bm9wZQ==",
        "%%%",
        # A timestamp with no UTC offset.
        base64.urlsafe_b64encode(f"2026-10-01T09:00:00|{uuid4()}".encode()).decode(),
    ],
)
def test_page_rejects_a_token_it_did_not_issue(repository: PrintJobRepository, token: str) -> None:
    with pytest.raises(InvalidPageToken):
        run(repository.page(10, token))
