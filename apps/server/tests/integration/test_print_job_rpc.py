from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from proto_utils.gen.server.v1.print_job_service_connect import PrintJobServiceASGIApplication

from api.domains.print_job.service import PrintJobService
from api.infrastructure.print_job_sql import (
    STUB_APPROVED_JOB_ID,
    STUB_SUBMITTED_JOB_ID,
    SqlPrintJobRepository,
    stub_print_jobs,
)
from api.main import app
from api.services.print_job_service import PrintJobServiceImplementation

_RPC = "/server.v1.PrintJobService"


@pytest.fixture
def client() -> TestClient:
    """A fresh store per test, so a transition in one test is not seen by the next."""
    service = PrintJobService(
        SqlPrintJobRepository(stub_print_jobs()), clock=lambda: datetime.now(UTC)
    )
    return TestClient(PrintJobServiceASGIApplication(PrintJobServiceImplementation(service)))


def _id(print_job_id: object) -> dict[str, str]:
    return {"value": str(print_job_id)}


def test_rpc_is_mounted_on_the_app() -> None:
    response = TestClient(app).post(
        f"/api{_RPC}/GetPrintJob", json={"printJobId": _id(STUB_SUBMITTED_JOB_ID)}
    )

    assert response.status_code == 200
    assert response.json()["printJob"]["status"] == "PRINT_JOB_STATUS_SUBMITTED"


def test_get_print_job_returns_the_job(client: TestClient) -> None:
    response = client.post(f"{_RPC}/GetPrintJob", json={"printJobId": _id(STUB_SUBMITTED_JOB_ID)})

    assert response.status_code == 200
    assert response.json()["printJob"]["id"] == _id(STUB_SUBMITTED_JOB_ID)


def test_get_print_job_reports_an_unknown_id(client: TestClient) -> None:
    unknown = "00000000-0000-4000-8000-0000000000ff"
    response = client.post(f"{_RPC}/GetPrintJob", json={"printJobId": {"value": unknown}})

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_get_print_job_rejects_a_malformed_id(client: TestClient) -> None:
    response = client.post(f"{_RPC}/GetPrintJob", json={"printJobId": {"value": "nope"}})

    assert response.status_code == 400
    assert response.json() == {"code": "invalid_argument", "message": "print_job_id must be a UUID"}


def test_start_review_moves_the_job_under_review(client: TestClient) -> None:
    response = client.post(
        f"{_RPC}/TransitionPrintJob",
        json={"printJobId": _id(STUB_SUBMITTED_JOB_ID), "startReview": {}},
    )

    assert response.status_code == 200
    assert response.json()["printJob"]["status"] == "PRINT_JOB_STATUS_UNDER_REVIEW"


def test_start_review_refused_by_the_rule(client: TestClient) -> None:
    response = client.post(
        f"{_RPC}/TransitionPrintJob",
        json={"printJobId": _id(STUB_APPROVED_JOB_ID), "startReview": {}},
    )

    assert response.json()["code"] == "failed_precondition"
