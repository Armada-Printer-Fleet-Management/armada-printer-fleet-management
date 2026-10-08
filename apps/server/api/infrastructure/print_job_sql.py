from collections.abc import Iterable
from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID

from core_domain.ddd import EntityNotFound
from core_domain.ids import PrintJobId, UserId
from core_domain.print_job import PrintJob, PrintJobStatus

STUB_STUDENT_ID = UserId(UUID("00000000-0000-4000-8000-000000000100"))
STUB_DRAFT_JOB_ID = PrintJobId(UUID("00000000-0000-4000-8000-000000000001"))
STUB_SUBMITTED_JOB_ID = PrintJobId(UUID("00000000-0000-4000-8000-000000000002"))
STUB_APPROVED_JOB_ID = PrintJobId(UUID("00000000-0000-4000-8000-000000000003"))
_STUB_TIME = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)


def stub_print_jobs() -> list[PrintJob]:
    # TODO
    def stub(print_job_id: PrintJobId, status: PrintJobStatus, notes: str) -> PrintJob:
        return PrintJob(print_job_id, STUB_STUDENT_ID, status, _STUB_TIME, _STUB_TIME, notes)

    return [
        stub(STUB_DRAFT_JOB_ID, PrintJobStatus.DRAFT, "Stub draft job"),
        stub(STUB_SUBMITTED_JOB_ID, PrintJobStatus.SUBMITTED, "Stub submitted job"),
        stub(STUB_APPROVED_JOB_ID, PrintJobStatus.APPROVED, "Stub approved job"),
    ]


class SqlPrintJobRepository:
    def __init__(self, print_jobs: Iterable[PrintJob] = ()) -> None:
        self._print_jobs = {print_job.id: print_job for print_job in print_jobs}

    async def get(self, entity_id: PrintJobId) -> PrintJob:
        # TODO: Replace this mock data
        if entity_id not in self._print_jobs:
            raise EntityNotFound(entity_id)
        # A copy, as a database would return, so a change is only stored once it is saved.
        return replace(self._print_jobs[entity_id])

    async def save(self, entity: PrintJob) -> None:
        # TODO: Replace this mock data
        self._print_jobs[entity.id] = replace(entity)
