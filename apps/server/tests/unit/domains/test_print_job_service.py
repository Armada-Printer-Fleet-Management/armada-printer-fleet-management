import pytest
from core_domain.ddd import EntityNotFound, RuleViolation
from core_domain.ids import FileId, PrinterId, PrinterQueueId, PrintJobId, UserId
from core_domain.print_job import PrintJobStatus

from api.domains.print_job.service import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, PrintJobService
from api.infrastructure.dev_data import (
    STUB_APPROVED_JOB_ID,
    STUB_DRAFT_JOB_ID,
    STUB_FINISHED_JOB_ID,
    STUB_PRINTER_QUEUE_ID,
    STUB_PRINTING_JOB_ID,
    STUB_SUBMITTED_JOB_ID,
    stub_print_jobs,
)
from api.infrastructure.print_job_memory import InMemoryPrintJobRepository
from tests.samples import NOW


@pytest.fixture
def service() -> PrintJobService:
    return PrintJobService(InMemoryPrintJobRepository(stub_print_jobs()), clock=lambda: NOW)


async def status(service: PrintJobService, print_job_id: PrintJobId) -> PrintJobStatus:
    return (await service.print_job(print_job_id)).status


async def test_print_job_returns_the_stored_job(service: PrintJobService) -> None:
    assert await status(service, STUB_SUBMITTED_JOB_ID) is PrintJobStatus.SUBMITTED


async def test_print_job_reports_an_unknown_id(service: PrintJobService) -> None:
    with pytest.raises(EntityNotFound):
        await service.print_job(PrintJobId.new())


async def test_create_saves_a_draft(service: PrintJobService) -> None:
    user_id = UserId.new()
    created = await service.create(user_id, "notes")

    stored = await service.print_job(created.id)
    assert (stored.status, stored.user_id, stored.created_at) == (
        PrintJobStatus.DRAFT,
        user_id,
        NOW,
    )


async def uploaded(_file_id: FileId) -> bool:
    return True


async def test_attach_new_file_then_submit(service: PrintJobService) -> None:
    file_id = FileId.new()

    async def new_file() -> FileId:
        return file_id

    await service.attach_new_file(STUB_DRAFT_JOB_ID, new_file)
    await service.submit(STUB_DRAFT_JOB_ID, uploaded, STUB_PRINTER_QUEUE_ID)

    stored = await service.print_job(STUB_DRAFT_JOB_ID)
    assert (stored.status, stored.file_id, stored.printer_queue_id, stored.updated_at) == (
        PrintJobStatus.SUBMITTED,
        file_id,
        STUB_PRINTER_QUEUE_ID,
        NOW,
    )


async def test_attach_new_file_creates_no_file_for_a_job_past_draft(
    service: PrintJobService,
) -> None:
    created: list[FileId] = []

    async def new_file() -> FileId:
        created.append(FileId.new())
        return created[-1]

    with pytest.raises(RuleViolation):
        await service.attach_new_file(STUB_SUBMITTED_JOB_ID, new_file)
    assert created == []


async def test_submit_checks_the_upload_of_the_jobs_own_file(service: PrintJobService) -> None:
    file_id = FileId.new()
    checked: list[FileId] = []

    async def new_file() -> FileId:
        return file_id

    async def is_uploaded(candidate: FileId) -> bool:
        checked.append(candidate)
        return True

    await service.attach_new_file(STUB_DRAFT_JOB_ID, new_file)
    await service.submit(STUB_DRAFT_JOB_ID, is_uploaded, STUB_PRINTER_QUEUE_ID)
    assert checked == [file_id]


async def test_submit_refused_by_the_rule_saves_nothing(service: PrintJobService) -> None:
    with pytest.raises(RuleViolation):
        await service.submit(STUB_DRAFT_JOB_ID, uploaded, STUB_PRINTER_QUEUE_ID)
    assert await status(service, STUB_DRAFT_JOB_ID) is PrintJobStatus.DRAFT


async def test_start_review_saves_the_change(service: PrintJobService) -> None:
    await service.start_review(STUB_SUBMITTED_JOB_ID)

    stored = await service.print_job(STUB_SUBMITTED_JOB_ID)
    assert stored.status is PrintJobStatus.UNDER_REVIEW
    assert stored.updated_at == NOW


async def test_start_review_refused_by_the_rule_saves_nothing(service: PrintJobService) -> None:
    with pytest.raises(RuleViolation):
        await service.start_review(STUB_APPROVED_JOB_ID)

    assert await status(service, STUB_APPROVED_JOB_ID) is PrintJobStatus.APPROVED


async def test_approve_saves_the_change(service: PrintJobService) -> None:
    await service.start_review(STUB_SUBMITTED_JOB_ID)
    await service.approve(STUB_SUBMITTED_JOB_ID)
    assert await status(service, STUB_SUBMITTED_JOB_ID) is PrintJobStatus.APPROVED


async def test_reject_saves_the_reason(service: PrintJobService) -> None:
    await service.start_review(STUB_SUBMITTED_JOB_ID)
    await service.reject(STUB_SUBMITTED_JOB_ID, "Too large")

    stored = await service.print_job(STUB_SUBMITTED_JOB_ID)
    assert (stored.status, stored.status_reason) == (PrintJobStatus.REJECTED, "Too large")


async def dispatched() -> bool:
    return True


async def test_assign_saves_the_printer(service: PrintJobService) -> None:
    printer_id = PrinterId.new()
    await service.assign(STUB_APPROVED_JOB_ID, printer_id, dispatched)

    stored = await service.print_job(STUB_APPROVED_JOB_ID)
    assert (stored.status, stored.printer_id) == (PrintJobStatus.ASSIGNED, printer_id)


async def test_assign_never_dispatches_a_job_that_is_not_approved(service: PrintJobService) -> None:
    calls: list[None] = []

    async def dispatch() -> bool:
        calls.append(None)
        return True

    with pytest.raises(RuleViolation):
        await service.assign(STUB_SUBMITTED_JOB_ID, PrinterId.new(), dispatch)
    assert calls == []


async def test_assign_saves_nothing_when_the_printer_refuses(service: PrintJobService) -> None:
    async def refuse() -> bool:
        raise RuleViolation("A PRINTING printer cannot take a print job")

    with pytest.raises(RuleViolation):
        await service.assign(STUB_APPROVED_JOB_ID, PrinterId.new(), refuse)
    assert await status(service, STUB_APPROVED_JOB_ID) is PrintJobStatus.APPROVED


async def test_complete_saves_the_change(service: PrintJobService) -> None:
    await service.complete(STUB_FINISHED_JOB_ID)

    stored = await service.print_job(STUB_FINISHED_JOB_ID)
    assert (stored.status, stored.updated_at) == (PrintJobStatus.COMPLETED, NOW)


async def test_complete_refused_by_the_rule_saves_nothing(service: PrintJobService) -> None:
    with pytest.raises(RuleViolation):
        await service.complete(STUB_PRINTING_JOB_ID)

    assert await status(service, STUB_PRINTING_JOB_ID) is PrintJobStatus.PRINTING


async def test_fail_saves_the_reason(service: PrintJobService) -> None:
    await service.fail(STUB_PRINTING_JOB_ID, "Spaghetti at layer 40")

    stored = await service.print_job(STUB_PRINTING_JOB_ID)
    assert (stored.status, stored.status_reason) == (PrintJobStatus.FAILED, "Spaghetti at layer 40")


async def test_move_to_queue_saves_the_new_queue(service: PrintJobService) -> None:
    queue_id = PrinterQueueId.new()

    await service.move_to_queue(STUB_APPROVED_JOB_ID, queue_id)

    assert (await service.print_job(STUB_APPROVED_JOB_ID)).printer_queue_id == queue_id


async def test_move_to_queue_refused_by_the_rule_saves_nothing(service: PrintJobService) -> None:
    with pytest.raises(RuleViolation):
        await service.move_to_queue(STUB_DRAFT_JOB_ID, PrinterQueueId.new())

    assert (await service.print_job(STUB_DRAFT_JOB_ID)).printer_queue_id is None


@pytest.mark.parametrize(
    ("requested", "applied"),
    [(0, DEFAULT_PAGE_SIZE), (2, 2), (MAX_PAGE_SIZE + 1, MAX_PAGE_SIZE)],
)
async def test_page_applies_the_default_and_the_cap(requested: int, applied: int) -> None:
    repository = InMemoryPrintJobRepository()
    service = PrintJobService(repository, clock=lambda: NOW)
    for _ in range(MAX_PAGE_SIZE + 1):
        await service.create(UserId.new(), "")

    assert len((await service.page(requested, "")).items) == applied
