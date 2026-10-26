import re
from datetime import UTC, datetime
from pathlib import Path

import pytest

from core_domain.ddd import RuleViolation
from core_domain.ids import FileId, PrinterId, PrinterQueueId, PrintJobId, UserId
from core_domain.print_job import PrintJob, PrintJobStatus

PROTO = Path(__file__).resolve().parents[2] / "proto" / "print_job" / "v1" / "print_job.proto"
CREATED = datetime(2026, 10, 1, tzinfo=UTC)
LATER = datetime(2026, 10, 2, tzinfo=UTC)


def test_status_mirrors_the_proto_enum() -> None:
    """Read as text, because core-domain may not depend on protobuf."""
    proto_values = re.findall(r"^\s*PRINT_JOB_STATUS_(\w+)\s*=", PROTO.read_text(), re.MULTILINE)
    assert [v for v in proto_values if v != "UNSPECIFIED"] == [s.name for s in PrintJobStatus]


def job(status: PrintJobStatus) -> PrintJob:
    return PrintJob(PrintJobId.new(), UserId.new(), status, CREATED, CREATED)


def test_start_review_moves_a_submitted_job_under_review() -> None:
    print_job = job(PrintJobStatus.SUBMITTED)
    assert print_job.can_start_review()

    print_job.start_review(LATER)

    assert print_job.status is PrintJobStatus.UNDER_REVIEW
    assert print_job.updated_at == LATER


@pytest.mark.parametrize("status", [s for s in PrintJobStatus if s is not PrintJobStatus.SUBMITTED])
def test_start_review_refuses_any_other_status(status: PrintJobStatus) -> None:
    print_job = job(status)
    assert not print_job.can_start_review()

    with pytest.raises(RuleViolation):
        print_job.start_review(LATER)
    assert print_job.status is status
    assert print_job.updated_at == CREATED


def test_create_starts_a_draft_with_no_file() -> None:
    user_id = UserId.new()
    print_job = PrintJob.create(user_id, "notes", CREATED)

    assert print_job.status is PrintJobStatus.DRAFT
    assert print_job.user_id == user_id
    assert print_job.user_notes == "notes"
    assert print_job.file_id is None
    assert print_job.created_at == print_job.updated_at == CREATED


def test_attach_file_links_a_draft_to_its_file() -> None:
    print_job = job(PrintJobStatus.DRAFT)
    file_id = FileId.new()

    print_job.attach_file(file_id, LATER)

    assert print_job.file_id == file_id
    assert print_job.updated_at == LATER


@pytest.mark.parametrize("status", [s for s in PrintJobStatus if s is not PrintJobStatus.DRAFT])
def test_attach_file_refuses_a_job_past_draft(status: PrintJobStatus) -> None:
    with pytest.raises(RuleViolation):
        job(status).attach_file(FileId.new(), LATER)


def test_require_can_attach_file_allows_a_draft() -> None:
    job(PrintJobStatus.DRAFT).require_can_attach_file()


@pytest.mark.parametrize("status", [s for s in PrintJobStatus if s is not PrintJobStatus.DRAFT])
def test_require_can_attach_file_refuses_a_job_past_draft(status: PrintJobStatus) -> None:
    with pytest.raises(RuleViolation, match=f"A {status.name} print job"):
        job(status).require_can_attach_file()


def test_submit_moves_a_draft_with_an_uploaded_file_to_submitted_in_a_queue() -> None:
    print_job = job(PrintJobStatus.DRAFT)
    print_job.attach_file(FileId.new(), CREATED)
    printer_queue_id = PrinterQueueId.new()

    print_job.submit(file_uploaded=True, printer_queue_id=printer_queue_id, now=LATER)

    assert print_job.status is PrintJobStatus.SUBMITTED
    assert print_job.printer_queue_id == printer_queue_id
    assert print_job.updated_at == LATER


def test_submit_refuses_a_draft_with_no_file() -> None:
    print_job = job(PrintJobStatus.DRAFT)
    assert not print_job.can_submit(file_uploaded=True)
    with pytest.raises(RuleViolation):
        print_job.submit(file_uploaded=True, printer_queue_id=PrinterQueueId.new(), now=LATER)


def test_submit_refuses_a_file_that_has_not_finished_uploading() -> None:
    print_job = job(PrintJobStatus.DRAFT)
    print_job.attach_file(FileId.new(), CREATED)
    with pytest.raises(RuleViolation):
        print_job.submit(file_uploaded=False, printer_queue_id=PrinterQueueId.new(), now=LATER)
    assert print_job.status is PrintJobStatus.DRAFT
    assert print_job.printer_queue_id is None


@pytest.mark.parametrize("status", [s for s in PrintJobStatus if s is not PrintJobStatus.DRAFT])
def test_submit_refuses_a_job_past_draft(status: PrintJobStatus) -> None:
    with pytest.raises(RuleViolation):
        job(status).submit(file_uploaded=True, printer_queue_id=PrinterQueueId.new(), now=LATER)


def test_move_to_queue_changes_the_queue_of_a_waiting_job() -> None:
    print_job = job(PrintJobStatus.APPROVED)
    printer_queue_id = PrinterQueueId.new()

    print_job.move_to_queue(printer_queue_id, LATER)

    assert print_job.printer_queue_id == printer_queue_id
    assert print_job.updated_at == LATER


def test_move_to_queue_refuses_a_job_already_on_a_printer() -> None:
    print_job = job(PrintJobStatus.ASSIGNED)
    with pytest.raises(RuleViolation):
        print_job.move_to_queue(PrinterQueueId.new(), LATER)
    assert print_job.printer_queue_id is None


def test_approve_moves_a_job_under_review_to_approved() -> None:
    print_job = job(PrintJobStatus.UNDER_REVIEW)
    print_job.approve(LATER)
    assert print_job.status is PrintJobStatus.APPROVED
    assert print_job.updated_at == LATER


@pytest.mark.parametrize(
    "status", [s for s in PrintJobStatus if s is not PrintJobStatus.UNDER_REVIEW]
)
def test_approve_and_reject_refuse_a_job_not_under_review(status: PrintJobStatus) -> None:
    with pytest.raises(RuleViolation):
        job(status).approve(LATER)
    with pytest.raises(RuleViolation):
        job(status).reject("reason", LATER)


def test_reject_records_the_reason() -> None:
    print_job = job(PrintJobStatus.UNDER_REVIEW)
    print_job.reject("Too large for any printer", LATER)
    assert print_job.status is PrintJobStatus.REJECTED
    assert print_job.status_reason == "Too large for any printer"


@pytest.mark.parametrize("reason", ["", "   "])
def test_reject_requires_a_reason(reason: str) -> None:
    print_job = job(PrintJobStatus.UNDER_REVIEW)
    with pytest.raises(RuleViolation):
        print_job.reject(reason, LATER)
    assert print_job.status is PrintJobStatus.UNDER_REVIEW


def test_assign_sets_the_printer_of_an_approved_job() -> None:
    print_job = job(PrintJobStatus.APPROVED)
    printer_id = PrinterId.new()

    print_job.assign(printer_id, dispatched=True, now=LATER)

    assert print_job.status is PrintJobStatus.ASSIGNED
    assert print_job.printer_id == printer_id


@pytest.mark.parametrize("status", [s for s in PrintJobStatus if s is not PrintJobStatus.APPROVED])
def test_assign_refuses_a_job_that_is_not_approved(status: PrintJobStatus) -> None:
    print_job = job(status)
    with pytest.raises(RuleViolation):
        print_job.assign(PrinterId.new(), dispatched=True, now=LATER)
    assert print_job.printer_id is None


def test_assign_refuses_until_the_printer_accepts_the_job() -> None:
    print_job = job(PrintJobStatus.APPROVED)
    with pytest.raises(RuleViolation):
        print_job.assign(PrinterId.new(), dispatched=False, now=LATER)
    assert print_job.status is PrintJobStatus.APPROVED


def test_start_printing_follows_the_printer_report() -> None:
    print_job = job(PrintJobStatus.ASSIGNED)
    print_job.start_printing(printer_printing=True, now=LATER)
    assert print_job.status is PrintJobStatus.PRINTING


def test_start_printing_refuses_until_the_printer_reports_it() -> None:
    print_job = job(PrintJobStatus.ASSIGNED)
    assert not print_job.can_start_printing(printer_printing=False)
    with pytest.raises(RuleViolation):
        print_job.start_printing(printer_printing=False, now=LATER)
    assert print_job.status is PrintJobStatus.ASSIGNED


def test_finish_follows_the_printer_report() -> None:
    print_job = job(PrintJobStatus.PRINTING)
    print_job.finish(printer_finished=True, now=LATER)
    assert print_job.status is PrintJobStatus.FINISHED


def test_finish_refuses_until_the_printer_reports_it() -> None:
    print_job = job(PrintJobStatus.PRINTING)
    with pytest.raises(RuleViolation):
        print_job.finish(printer_finished=False, now=LATER)
    assert print_job.status is PrintJobStatus.PRINTING


def test_complete_accepts_a_finished_job() -> None:
    print_job = job(PrintJobStatus.FINISHED)
    print_job.complete(LATER)
    assert print_job.status is PrintJobStatus.COMPLETED


@pytest.mark.parametrize("status", [s for s in PrintJobStatus if s is not PrintJobStatus.FINISHED])
def test_complete_refuses_a_job_that_has_not_finished(status: PrintJobStatus) -> None:
    with pytest.raises(RuleViolation):
        job(status).complete(LATER)


def test_fail_records_the_reason() -> None:
    print_job = job(PrintJobStatus.FINISHED)
    print_job.fail("Layers shifted halfway up", LATER)
    assert print_job.status is PrintJobStatus.FAILED
    assert print_job.status_reason == "Layers shifted halfway up"


@pytest.mark.parametrize(
    "status",
    [
        s
        for s in PrintJobStatus
        if s not in (PrintJobStatus.ASSIGNED, PrintJobStatus.PRINTING, PrintJobStatus.FINISHED)
    ],
)
def test_fail_refuses_a_job_that_is_not_on_a_printer(status: PrintJobStatus) -> None:
    with pytest.raises(RuleViolation):
        job(status).fail("reason", LATER)


def test_fail_requires_a_reason() -> None:
    print_job = job(PrintJobStatus.PRINTING)
    with pytest.raises(RuleViolation):
        print_job.fail("  ", LATER)
    assert print_job.status is PrintJobStatus.PRINTING
