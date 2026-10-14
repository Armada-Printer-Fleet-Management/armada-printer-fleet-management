# Stub: seed data for the in-memory repositories, so a freshly started server has jobs in each
# early status for the web and desktop apps to work against. Remove it once the server runs on
# its real database, which seeds through migrations or fixtures instead.
from datetime import UTC, datetime, timedelta
from uuid import UUID

from core_domain.file import File, FileType
from core_domain.ids import FileId, PrintJobId, UserId
from core_domain.print_job import PrintJob, PrintJobStatus

STUB_STUDENT_ID = UserId(UUID("00000000-0000-4000-8000-000000000100"))
STUB_DRAFT_JOB_ID = PrintJobId(UUID("00000000-0000-4000-8000-000000000001"))
STUB_SUBMITTED_JOB_ID = PrintJobId(UUID("00000000-0000-4000-8000-000000000002"))
STUB_APPROVED_JOB_ID = PrintJobId(UUID("00000000-0000-4000-8000-000000000003"))
STUB_SUBMITTED_FILE_ID = FileId(UUID("00000000-0000-4000-8000-000000000201"))
STUB_APPROVED_FILE_ID = FileId(UUID("00000000-0000-4000-8000-000000000202"))
_STUB_TIME = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)


def stub_print_jobs() -> list[PrintJob]:
    def stub(
        minutes: int, print_job_id: PrintJobId, status: PrintJobStatus, file_id: FileId | None
    ) -> PrintJob:
        time = _STUB_TIME + timedelta(minutes=minutes)
        notes = f"Stub {status.name.lower()} job"
        return PrintJob(print_job_id, STUB_STUDENT_ID, status, time, time, notes, file_id=file_id)

    return [
        stub(0, STUB_APPROVED_JOB_ID, PrintJobStatus.APPROVED, STUB_APPROVED_FILE_ID),
        stub(1, STUB_SUBMITTED_JOB_ID, PrintJobStatus.SUBMITTED, STUB_SUBMITTED_FILE_ID),
        stub(2, STUB_DRAFT_JOB_ID, PrintJobStatus.DRAFT, None),
    ]


def stub_files() -> list[File]:
    def stub(file_id: FileId, filename: str) -> File:
        return File(file_id, filename, FileType.GCODE, 1024, "0" * 64, _STUB_TIME, _STUB_TIME)

    return [
        stub(STUB_SUBMITTED_FILE_ID, "stub-submitted.gcode"),
        stub(STUB_APPROVED_FILE_ID, "stub-approved.gcode"),
    ]
