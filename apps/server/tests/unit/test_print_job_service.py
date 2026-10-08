import asyncio
from datetime import UTC, datetime

import pytest
from core_domain.ddd import EntityNotFound, RuleViolation
from core_domain.ids import PrintJobId
from core_domain.print_job import PrintJobStatus

from api.domains.print_job.service import PrintJobService
from api.infrastructure.print_job_sql import (
    STUB_APPROVED_JOB_ID,
    STUB_SUBMITTED_JOB_ID,
    SqlPrintJobRepository,
    stub_print_jobs,
)

NOW = datetime(2026, 10, 7, 12, 0, tzinfo=UTC)


@pytest.fixture
def service() -> PrintJobService:
    return PrintJobService(SqlPrintJobRepository(stub_print_jobs()), clock=lambda: NOW)


def test_print_job_returns_the_stored_job(service: PrintJobService) -> None:
    print_job = asyncio.run(service.print_job(STUB_SUBMITTED_JOB_ID))
    assert print_job.status is PrintJobStatus.SUBMITTED


def test_print_job_reports_an_unknown_id(service: PrintJobService) -> None:
    with pytest.raises(EntityNotFound):
        asyncio.run(service.print_job(PrintJobId.new()))


def test_start_review_saves_the_change(service: PrintJobService) -> None:
    asyncio.run(service.start_review(STUB_SUBMITTED_JOB_ID))

    stored = asyncio.run(service.print_job(STUB_SUBMITTED_JOB_ID))
    assert stored.status is PrintJobStatus.UNDER_REVIEW
    assert stored.updated_at == NOW


def test_start_review_refused_by_the_rule_saves_nothing(service: PrintJobService) -> None:
    with pytest.raises(RuleViolation):
        asyncio.run(service.start_review(STUB_APPROVED_JOB_ID))

    assert asyncio.run(service.print_job(STUB_APPROVED_JOB_ID)).status is PrintJobStatus.APPROVED
