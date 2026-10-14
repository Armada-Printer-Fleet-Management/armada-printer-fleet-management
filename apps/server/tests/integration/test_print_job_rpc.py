from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import pytest
from core_domain.file import File
from fastapi.testclient import TestClient
from proto_utils.gen.server.v1.print_job_service_connect import PrintJobServiceASGIApplication

from api.domains.file.service import FileService
from api.domains.print_job.service import PrintJobService
from api.infrastructure.file_memory import InMemoryFileRepository
from api.infrastructure.file_storage_mock import MockFileStorage
from api.infrastructure.print_job_memory import InMemoryPrintJobRepository
from api.infrastructure.stub_data import (
    STUB_APPROVED_JOB_ID,
    STUB_DRAFT_JOB_ID,
    STUB_STUDENT_ID,
    STUB_SUBMITTED_FILE_ID,
    STUB_SUBMITTED_JOB_ID,
    stub_files,
    stub_print_jobs,
)
from api.main import app
from api.services.print_job_service import PrintJobServiceImplementation

_RPC = "/server.v1.PrintJobService"
_METADATA = {
    "filename": "part.gcode",
    "sizeBytes": "1024",
    "sha256": "e" * 64,
    "fileType": "FILE_TYPE_GCODE",
}

type Json = dict[str, Any]


@pytest.fixture
def client() -> TestClient:
    """A fresh store per test, so a change in one test is not seen by the next."""

    def clock() -> datetime:
        return datetime.now(UTC)

    return _client(stub_files(), clock)


def _client(files: list[File], clock: Callable[[], datetime]) -> TestClient:
    print_jobs = PrintJobService(InMemoryPrintJobRepository(stub_print_jobs()), clock)
    file_service = FileService(InMemoryFileRepository(files), MockFileStorage(), clock)
    handler = PrintJobServiceImplementation(
        print_jobs, file_service, caller=lambda: STUB_STUDENT_ID
    )
    return TestClient(PrintJobServiceASGIApplication(handler))


def _id(entity_id: object) -> dict[str, str]:
    return {"value": str(entity_id)}


def call(client: TestClient, rpc: str, body: Json, expect: int = 200) -> Json:
    response = client.post(f"{_RPC}/{rpc}", json=body)
    assert response.status_code == expect, response.text
    result: Json = response.json()
    return result


def test_rpc_is_mounted_on_the_app() -> None:
    response = TestClient(app).post(
        f"/api{_RPC}/GetPrintJob", json={"printJobId": _id(STUB_SUBMITTED_JOB_ID)}
    )

    assert response.status_code == 200
    assert response.json()["printJob"]["status"] == "PRINT_JOB_STATUS_SUBMITTED"


def test_get_print_job_returns_the_job_and_its_file(client: TestClient) -> None:
    body = call(client, "GetPrintJob", {"printJobId": _id(STUB_SUBMITTED_JOB_ID)})

    assert body["printJob"]["id"] == _id(STUB_SUBMITTED_JOB_ID)
    assert body["file"]["id"] == _id(STUB_SUBMITTED_FILE_ID)


def test_get_print_job_leaves_file_unset_without_an_upload(client: TestClient) -> None:
    body = call(client, "GetPrintJob", {"printJobId": _id(STUB_DRAFT_JOB_ID)})
    assert "file" not in body


def test_get_print_job_omits_a_missing_file_record() -> None:
    client = _client([], lambda: datetime.now(UTC))
    body = call(client, "GetPrintJob", {"printJobId": _id(STUB_SUBMITTED_JOB_ID)})

    assert body["printJob"]["fileId"] == _id(STUB_SUBMITTED_FILE_ID)
    assert "file" not in body


def test_get_print_job_reports_an_unknown_id(client: TestClient) -> None:
    unknown = "00000000-0000-4000-8000-0000000000ff"
    body = call(client, "GetPrintJob", {"printJobId": {"value": unknown}}, expect=404)
    assert body["code"] == "not_found"


def test_get_print_job_rejects_a_malformed_id(client: TestClient) -> None:
    body = call(client, "GetPrintJob", {"printJobId": {"value": "nope"}}, expect=400)
    assert body == {"code": "invalid_argument", "message": "print_job_id must be a UUID"}


def test_a_job_goes_from_creation_to_a_printer(client: TestClient) -> None:
    created = call(client, "CreatePrintJob", {"userNotes": "Please use PLA"})["printJob"]
    assert created["status"] == "PRINT_JOB_STATUS_DRAFT"
    assert created["userId"] == _id(STUB_STUDENT_ID)
    job = {"printJobId": created["id"]}

    slot = call(client, "CreatePrintJobUpload", {**job, "metadata": _METADATA})["slot"]
    assert slot["fileId"]["value"] in slot["uploadUrl"]

    submitted = call(client, "SubmitPrintJob", job)
    assert submitted["printJob"]["status"] == "PRINT_JOB_STATUS_SUBMITTED"
    assert submitted["file"]["id"] == slot["fileId"]

    call(client, "TransitionPrintJob", {**job, "startReview": {}})
    call(client, "TransitionPrintJob", {**job, "approve": {}})
    printer = _id("00000000-0000-4000-8000-000000000301")
    assigned = call(client, "TransitionPrintJob", {**job, "assign": {"printerId": printer}})

    assert assigned["printJob"]["status"] == "PRINT_JOB_STATUS_ASSIGNED"
    assert assigned["printJob"]["printerId"] == printer


def test_a_second_upload_replaces_the_file(client: TestClient) -> None:
    job = {"printJobId": _id(STUB_DRAFT_JOB_ID), "metadata": _METADATA}
    first = call(client, "CreatePrintJobUpload", job)["slot"]["fileId"]
    second = call(client, "CreatePrintJobUpload", job)["slot"]["fileId"]

    body = call(client, "GetPrintJob", {"printJobId": _id(STUB_DRAFT_JOB_ID)})
    assert first != second
    assert body["printJob"]["fileId"] == second


def test_upload_refused_for_a_job_past_draft(client: TestClient) -> None:
    job = {"printJobId": _id(STUB_SUBMITTED_JOB_ID), "metadata": _METADATA}
    body = call(client, "CreatePrintJobUpload", job, expect=400)
    assert body["code"] == "failed_precondition"


@pytest.mark.parametrize(
    "metadata",
    [
        {**_METADATA, "fileType": "FILE_TYPE_UNSPECIFIED"},
        {**_METADATA, "sizeBytes": "0"},
        {**_METADATA, "sha256": "not a hash"},
        {**_METADATA, "filename": ""},
    ],
)
def test_upload_rejects_bad_metadata(client: TestClient, metadata: Json) -> None:
    job = {"printJobId": _id(STUB_DRAFT_JOB_ID), "metadata": metadata}
    body = call(client, "CreatePrintJobUpload", job, expect=400)
    assert body["code"] == "invalid_argument"

    unchanged = call(client, "GetPrintJob", {"printJobId": _id(STUB_DRAFT_JOB_ID)})
    assert "fileId" not in unchanged["printJob"]


def test_submit_refused_without_an_upload(client: TestClient) -> None:
    body = call(client, "SubmitPrintJob", {"printJobId": _id(STUB_DRAFT_JOB_ID)}, expect=400)
    assert body["code"] == "failed_precondition"


def test_start_review_refused_by_the_rule(client: TestClient) -> None:
    job = {"printJobId": _id(STUB_APPROVED_JOB_ID), "startReview": {}}
    assert call(client, "TransitionPrintJob", job, expect=400)["code"] == "failed_precondition"


def test_reject_records_the_reason(client: TestClient) -> None:
    job = {"printJobId": _id(STUB_SUBMITTED_JOB_ID)}
    call(client, "TransitionPrintJob", {**job, "startReview": {}})

    body = call(client, "TransitionPrintJob", {**job, "reject": {"reason": "Too large"}})

    assert body["printJob"]["status"] == "PRINT_JOB_STATUS_REJECTED"
    assert body["printJob"]["statusReason"] == "Too large"


def test_reject_refused_without_a_reason(client: TestClient) -> None:
    job = {"printJobId": _id(STUB_SUBMITTED_JOB_ID)}
    call(client, "TransitionPrintJob", {**job, "startReview": {}})

    body = call(client, "TransitionPrintJob", {**job, "reject": {}}, expect=400)
    assert body["code"] == "failed_precondition"


def test_assign_rejects_a_malformed_printer_id(client: TestClient) -> None:
    job = {"printJobId": _id(STUB_APPROVED_JOB_ID), "assign": {"printerId": {"value": "x"}}}
    body = call(client, "TransitionPrintJob", job, expect=400)
    assert body == {"code": "invalid_argument", "message": "printer_id must be a UUID"}


def test_transition_requires_an_action(client: TestClient) -> None:
    body = call(client, "TransitionPrintJob", {"printJobId": _id(STUB_APPROVED_JOB_ID)}, 400)
    assert body["code"] == "invalid_argument"


def test_list_pages_through_every_job_with_its_files(client: TestClient) -> None:
    first = call(client, "ListPrintJobs", {"page": {"pageSize": 2}})
    token = first["page"]["nextPageToken"]
    second = call(client, "ListPrintJobs", {"page": {"pageSize": 2, "pageToken": token}})

    ids = [job["id"] for page in (first, second) for job in page["printJobs"]]
    assert ids == [_id(STUB_DRAFT_JOB_ID), _id(STUB_SUBMITTED_JOB_ID), _id(STUB_APPROVED_JOB_ID)]
    assert [file["id"] for file in first["files"]] == [_id(STUB_SUBMITTED_FILE_ID)]
    assert "nextPageToken" not in second.get("page", {})


def test_list_rejects_a_bad_page_token(client: TestClient) -> None:
    body = call(client, "ListPrintJobs", {"page": {"pageToken": "nope"}}, expect=400)
    assert body["code"] == "invalid_argument"
