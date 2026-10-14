import asyncio
from datetime import UTC, datetime

import pytest
from core_domain.ddd import EntityNotFound, RuleViolation
from core_domain.ids import FileId, PrinterId, PrintJobId, UserId
from core_domain.print_job import PrintJobStatus

from api.domains.print_job.service import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, PrintJobService
from api.infrastructure.print_job_memory import InMemoryPrintJobRepository
from api.infrastructure.stub_data import (
    STUB_APPROVED_JOB_ID,
    STUB_DRAFT_JOB_ID,
    STUB_SUBMITTED_JOB_ID,
    stub_print_jobs,
)

NOW = datetime(2026, 10, 7, 12, 0, tzinfo=UTC)


@pytest.fixture
def service() -> PrintJobService:
    return PrintJobService(InMemoryPrintJobRepository(stub_print_jobs()), clock=lambda: NOW)


def status(service: PrintJobService, print_job_id: PrintJobId) -> PrintJobStatus:
    return asyncio.run(service.print_job(print_job_id)).status


def test_print_job_returns_the_stored_job(service: PrintJobService) -> None:
    assert status(service, STUB_SUBMITTED_JOB_ID) is PrintJobStatus.SUBMITTED


def test_print_job_reports_an_unknown_id(service: PrintJobService) -> None:
    with pytest.raises(EntityNotFound):
        asyncio.run(service.print_job(PrintJobId.new()))


def test_create_saves_a_draft(service: PrintJobService) -> None:
    user_id = UserId.new()
    created = asyncio.run(service.create(user_id, "notes"))

    stored = asyncio.run(service.print_job(created.id))
    assert (stored.status, stored.user_id, stored.created_at) == (
        PrintJobStatus.DRAFT,
        user_id,
        NOW,
    )


async def uploaded(_file_id: FileId) -> bool:
    return True


def test_attach_new_file_then_submit(service: PrintJobService) -> None:
    file_id = FileId.new()

    async def new_file() -> FileId:
        return file_id

    asyncio.run(service.attach_new_file(STUB_DRAFT_JOB_ID, new_file))
    asyncio.run(service.submit(STUB_DRAFT_JOB_ID, uploaded))

    stored = asyncio.run(service.print_job(STUB_DRAFT_JOB_ID))
    assert (stored.status, stored.file_id, stored.updated_at) == (
        PrintJobStatus.SUBMITTED,
        file_id,
        NOW,
    )


def test_attach_new_file_creates_no_file_for_a_job_past_draft(service: PrintJobService) -> None:
    created: list[FileId] = []

    async def new_file() -> FileId:
        created.append(FileId.new())
        return created[-1]

    with pytest.raises(RuleViolation):
        asyncio.run(service.attach_new_file(STUB_SUBMITTED_JOB_ID, new_file))
    assert created == []


def test_submit_checks_the_upload_of_the_jobs_own_file(service: PrintJobService) -> None:
    file_id = FileId.new()
    checked: list[FileId] = []

    async def new_file() -> FileId:
        return file_id

    async def is_uploaded(candidate: FileId) -> bool:
        checked.append(candidate)
        return True

    asyncio.run(service.attach_new_file(STUB_DRAFT_JOB_ID, new_file))
    asyncio.run(service.submit(STUB_DRAFT_JOB_ID, is_uploaded))
    assert checked == [file_id]


def test_submit_refused_by_the_rule_saves_nothing(service: PrintJobService) -> None:
    with pytest.raises(RuleViolation):
        asyncio.run(service.submit(STUB_DRAFT_JOB_ID, uploaded))
    assert status(service, STUB_DRAFT_JOB_ID) is PrintJobStatus.DRAFT


def test_start_review_saves_the_change(service: PrintJobService) -> None:
    asyncio.run(service.start_review(STUB_SUBMITTED_JOB_ID))

    stored = asyncio.run(service.print_job(STUB_SUBMITTED_JOB_ID))
    assert stored.status is PrintJobStatus.UNDER_REVIEW
    assert stored.updated_at == NOW


def test_start_review_refused_by_the_rule_saves_nothing(service: PrintJobService) -> None:
    with pytest.raises(RuleViolation):
        asyncio.run(service.start_review(STUB_APPROVED_JOB_ID))

    assert status(service, STUB_APPROVED_JOB_ID) is PrintJobStatus.APPROVED


def test_approve_saves_the_change(service: PrintJobService) -> None:
    asyncio.run(service.start_review(STUB_SUBMITTED_JOB_ID))
    asyncio.run(service.approve(STUB_SUBMITTED_JOB_ID))
    assert status(service, STUB_SUBMITTED_JOB_ID) is PrintJobStatus.APPROVED


def test_reject_saves_the_reason(service: PrintJobService) -> None:
    asyncio.run(service.start_review(STUB_SUBMITTED_JOB_ID))
    asyncio.run(service.reject(STUB_SUBMITTED_JOB_ID, "Too large"))

    stored = asyncio.run(service.print_job(STUB_SUBMITTED_JOB_ID))
    assert (stored.status, stored.status_reason) == (PrintJobStatus.REJECTED, "Too large")


def test_assign_saves_the_printer(service: PrintJobService) -> None:
    printer_id = PrinterId.new()
    asyncio.run(service.assign(STUB_APPROVED_JOB_ID, printer_id))

    stored = asyncio.run(service.print_job(STUB_APPROVED_JOB_ID))
    assert (stored.status, stored.printer_id) == (PrintJobStatus.ASSIGNED, printer_id)


@pytest.mark.parametrize(
    ("requested", "applied"),
    [(0, DEFAULT_PAGE_SIZE), (2, 2), (MAX_PAGE_SIZE + 1, MAX_PAGE_SIZE)],
)
def test_page_applies_the_default_and_the_cap(requested: int, applied: int) -> None:
    repository = InMemoryPrintJobRepository()
    service = PrintJobService(repository, clock=lambda: NOW)
    for _ in range(MAX_PAGE_SIZE + 1):
        asyncio.run(service.create(UserId.new(), ""))

    assert len(asyncio.run(service.page(requested, "")).items) == applied
