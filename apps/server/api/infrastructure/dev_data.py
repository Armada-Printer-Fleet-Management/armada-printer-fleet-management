"""Development data: what the in-memory repositories start with, what the tests work against, and
what dev_seed.py writes into the development database. One set, so every route to it agrees."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from core_domain.file import File, FileType
from core_domain.ids import FileId, PrinterId, PrinterQueueId, PrintJobId, UserId
from core_domain.print_job import PrintJob, PrintJobStatus
from core_domain.printer import Printer, PrinterStatus
from core_domain.printer_queue import PrinterQueue
from proto_utils.gen.user.v1 import user_pb2

STUB_STUDENT_ID = UserId(UUID("00000000-0000-4000-8000-000000000100"))
STUB_STAFF_ID = UserId(UUID("00000000-0000-4000-8000-000000000101"))
# Stub: placeholders for the users' Keycloak subjects. Replace them with real subjects once users
# are created by signing in through Keycloak.
_STUB_STUDENT_KEYCLOAK_ID = UUID("00000000-0000-4000-8000-000000000110")
_STUB_STAFF_KEYCLOAK_ID = UUID("00000000-0000-4000-8000-000000000111")
STUB_DRAFT_JOB_ID = PrintJobId(UUID("00000000-0000-4000-8000-000000000001"))
STUB_SUBMITTED_JOB_ID = PrintJobId(UUID("00000000-0000-4000-8000-000000000002"))
STUB_APPROVED_JOB_ID = PrintJobId(UUID("00000000-0000-4000-8000-000000000003"))
STUB_PRINTING_JOB_ID = PrintJobId(UUID("00000000-0000-4000-8000-000000000004"))
STUB_FINISHED_JOB_ID = PrintJobId(UUID("00000000-0000-4000-8000-000000000005"))
STUB_SUBMITTED_FILE_ID = FileId(UUID("00000000-0000-4000-8000-000000000201"))
STUB_APPROVED_FILE_ID = FileId(UUID("00000000-0000-4000-8000-000000000202"))
STUB_PRINTING_FILE_ID = FileId(UUID("00000000-0000-4000-8000-000000000203"))
STUB_FINISHED_FILE_ID = FileId(UUID("00000000-0000-4000-8000-000000000204"))
STUB_IDLE_PRINTER_ID = PrinterId(UUID("00000000-0000-4000-8000-000000000301"))
STUB_SECOND_IDLE_PRINTER_ID = PrinterId(UUID("00000000-0000-4000-8000-000000000302"))
STUB_PRINTING_PRINTER_ID = PrinterId(UUID("00000000-0000-4000-8000-000000000303"))
STUB_FINISHED_PRINTER_ID = PrinterId(UUID("00000000-0000-4000-8000-000000000304"))
STUB_OFFLINE_PRINTER_ID = PrinterId(UUID("00000000-0000-4000-8000-000000000305"))
# The mock printer server reports this one as faulted partway through any print.
STUB_FAULTY_PRINTER_ID = PrinterId(UUID("00000000-0000-4000-8000-000000000306"))
STUB_PRINTER_QUEUE_ID = PrinterQueueId(UUID("00000000-0000-4000-8000-000000000401"))
STUB_FLEET_SECTION_ID = UUID("00000000-0000-4000-8000-000000000601")
_STUB_TIME = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)


# Users and fleet sections have no domain entity, so they are plain records only the seed reads.
@dataclass(frozen=True)
class StubUser:
    id: UserId
    keycloak_user_id: UUID
    email: str
    display_name: str
    role: user_pb2.UserRole


@dataclass(frozen=True)
class StubFleetSection:
    id: UUID
    name: str


def stub_users() -> list[StubUser]:
    return [
        StubUser(
            STUB_STUDENT_ID,
            _STUB_STUDENT_KEYCLOAK_ID,
            "student@example.com",
            "Stub Student",
            user_pb2.USER_ROLE_STUDENT,
        ),
        StubUser(
            STUB_STAFF_ID,
            _STUB_STAFF_KEYCLOAK_ID,
            "staff@example.com",
            "Stub Staff",
            user_pb2.USER_ROLE_STAFF,
        ),
    ]


def stub_fleet_sections() -> list[StubFleetSection]:
    return [StubFleetSection(STUB_FLEET_SECTION_ID, "Default section")]


def stub_print_jobs() -> list[PrintJob]:
    def stub(
        minutes: int,
        print_job_id: PrintJobId,
        status: PrintJobStatus,
        file_id: FileId | None,
        printer_id: PrinterId | None = None,
    ) -> PrintJob:
        time = _STUB_TIME + timedelta(minutes=minutes)
        notes = f"Stub {status.name.lower()} job"
        printer_queue_id = None if status is PrintJobStatus.DRAFT else STUB_PRINTER_QUEUE_ID
        return PrintJob(
            print_job_id,
            STUB_STUDENT_ID,
            status,
            time,
            time,
            notes,
            printer_queue_id=printer_queue_id,
            file_id=file_id,
            printer_id=printer_id,
        )

    return [
        stub(
            -2,
            STUB_FINISHED_JOB_ID,
            PrintJobStatus.FINISHED,
            STUB_FINISHED_FILE_ID,
            STUB_FINISHED_PRINTER_ID,
        ),
        stub(
            -1,
            STUB_PRINTING_JOB_ID,
            PrintJobStatus.PRINTING,
            STUB_PRINTING_FILE_ID,
            STUB_PRINTING_PRINTER_ID,
        ),
        stub(0, STUB_APPROVED_JOB_ID, PrintJobStatus.APPROVED, STUB_APPROVED_FILE_ID),
        stub(1, STUB_SUBMITTED_JOB_ID, PrintJobStatus.SUBMITTED, STUB_SUBMITTED_FILE_ID),
        stub(2, STUB_DRAFT_JOB_ID, PrintJobStatus.DRAFT, None),
    ]


def stub_files() -> list[File]:
    def stub(file_id: FileId, filename: str) -> File:
        return File(
            file_id,
            STUB_STUDENT_ID,
            filename,
            FileType.GCODE,
            1024,
            "0" * 64,
            _STUB_TIME,
            _STUB_TIME,
        )

    return [
        stub(STUB_SUBMITTED_FILE_ID, "stub-submitted.gcode"),
        stub(STUB_APPROVED_FILE_ID, "stub-approved.gcode"),
        stub(STUB_PRINTING_FILE_ID, "stub-printing.gcode"),
        stub(STUB_FINISHED_FILE_ID, "stub-finished.gcode"),
    ]


def stub_printer_queues() -> list[PrinterQueue]:
    return [PrinterQueue(STUB_PRINTER_QUEUE_ID, "General", True, _STUB_TIME, _STUB_TIME)]


def stub_printers() -> list[Printer]:
    def stub(
        number: int,
        printer_id: PrinterId,
        status: PrinterStatus,
        print_job_id: PrintJobId | None = None,
        progress_percent: int | None = None,
    ) -> Printer:
        return Printer(
            printer_id,
            f"Stub printer {number}",
            "Stub model",
            status,
            _STUB_TIME,
            _STUB_TIME,
            print_job_id,
            progress_percent,
        )

    return [
        stub(1, STUB_IDLE_PRINTER_ID, PrinterStatus.IDLE),
        stub(2, STUB_SECOND_IDLE_PRINTER_ID, PrinterStatus.IDLE),
        stub(3, STUB_PRINTING_PRINTER_ID, PrinterStatus.PRINTING, STUB_PRINTING_JOB_ID, 0),
        stub(4, STUB_FINISHED_PRINTER_ID, PrinterStatus.FINISHED, STUB_FINISHED_JOB_ID, 100),
        stub(5, STUB_OFFLINE_PRINTER_ID, PrinterStatus.OFFLINE),
        stub(6, STUB_FAULTY_PRINTER_ID, PrinterStatus.IDLE),
    ]
