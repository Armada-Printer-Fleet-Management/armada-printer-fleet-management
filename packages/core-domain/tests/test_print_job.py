import re
from datetime import UTC, datetime
from pathlib import Path

import pytest

from core_domain.ddd import RuleViolation
from core_domain.ids import PrintJobId, UserId
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
