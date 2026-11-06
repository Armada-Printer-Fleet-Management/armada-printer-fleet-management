from collections.abc import Callable
from datetime import UTC, datetime

import pytest
from core_domain.content_asset import File
from fastapi.testclient import TestClient

from api.infrastructure.dev_data import (
    STUB_APPROVED_FILE_ID,
    STUB_APPROVED_JOB_ID,
    STUB_DRAFT_JOB_ID,
    STUB_FINISHED_JOB_ID,
    STUB_IDLE_PRINTER_ID,
    STUB_PRINTING_JOB_ID,
    STUB_SUBMITTED_FILE_ID,
    STUB_SUBMITTED_JOB_ID,
    stub_files,
)
from tests.print_jobs import METADATA, PRINT_JOB_RPC, call, fake_client_and_poller
from tests.rpc import Json, id_json


@pytest.fixture
def client() -> TestClient:
    """A fresh store per test, so a change in one test is not seen by the next."""

    def clock() -> datetime:
        return datetime.now(UTC)

    return _client(stub_files(), clock)


def _client(files: list[File], clock: Callable[[], datetime]) -> TestClient:
    return fake_client_and_poller(files, clock)[0]


def test_get_print_job_returns_the_job_and_its_file(client: TestClient) -> None:
    body = call(client, "GetPrintJob", {"printJobId": id_json(STUB_SUBMITTED_JOB_ID)})

    assert body["printJob"]["id"] == id_json(STUB_SUBMITTED_JOB_ID)
    assert body["file"]["id"] == id_json(STUB_SUBMITTED_FILE_ID)


def test_get_print_job_leaves_file_unset_without_an_upload(client: TestClient) -> None:
    body = call(client, "GetPrintJob", {"printJobId": id_json(STUB_DRAFT_JOB_ID)})
    assert "file" not in body


def test_get_print_job_omits_a_missing_file_record() -> None:
    client = _client([], lambda: datetime.now(UTC))
    body = call(client, "GetPrintJob", {"printJobId": id_json(STUB_SUBMITTED_JOB_ID)})

    assert body["printJob"]["fileId"] == id_json(STUB_SUBMITTED_FILE_ID)
    assert "file" not in body


def test_get_print_job_reports_an_unknown_id(client: TestClient) -> None:
    unknown = "00000000-0000-4000-8000-0000000000ff"
    body = call(client, "GetPrintJob", {"printJobId": {"value": unknown}}, expect=404)
    assert body["code"] == "not_found"


def test_get_print_job_rejects_a_malformed_id(client: TestClient) -> None:
    body = call(client, "GetPrintJob", {"printJobId": {"value": "nope"}}, expect=400)
    assert body == {"code": "invalid_argument", "message": "print_job_id must be a UUID"}


def test_assign_refused_by_a_busy_printer(client: TestClient) -> None:
    busy = id_json(STUB_IDLE_PRINTER_ID)
    call(
        client,
        "TransitionPrintJob",
        {"printJobId": id_json(STUB_APPROVED_JOB_ID), "assign": {"printerId": busy}},
    )
    call(
        client,
        "TransitionPrintJob",
        {"printJobId": id_json(STUB_SUBMITTED_JOB_ID), "startReview": {}},
    )
    call(
        client, "TransitionPrintJob", {"printJobId": id_json(STUB_SUBMITTED_JOB_ID), "approve": {}}
    )

    second = {"printJobId": id_json(STUB_SUBMITTED_JOB_ID), "assign": {"printerId": busy}}
    assert call(client, "TransitionPrintJob", second, expect=400)["code"] == "failed_precondition"
    unchanged = call(client, "GetPrintJob", {"printJobId": id_json(STUB_SUBMITTED_JOB_ID)})
    assert unchanged["printJob"]["status"] == "PRINT_JOB_STATUS_APPROVED"


def test_move_to_queue_refuses_an_unknown_queue(client: TestClient) -> None:
    unknown = {"value": "00000000-0000-4000-8000-0000000004ff"}
    job = {"printJobId": id_json(STUB_APPROVED_JOB_ID), "moveToQueue": {"printerQueueId": unknown}}
    assert call(client, "TransitionPrintJob", job, expect=404)["code"] == "not_found"


def test_upload_url_is_https_behind_a_proxy_that_terminates_it(client: TestClient) -> None:
    response = client.post(
        f"{PRINT_JOB_RPC}/CreatePrintJobUpload",
        json={"printJobId": id_json(STUB_DRAFT_JOB_ID), "metadata": METADATA},
        headers={"Host": "fleet.example.test", "X-Forwarded-Proto": "https"},
    )

    assert response.json()["slot"]["uploadUrl"].startswith("https://fleet.example.test/api/files/")


def test_a_second_upload_replaces_the_file(client: TestClient) -> None:
    job = {"printJobId": id_json(STUB_DRAFT_JOB_ID), "metadata": METADATA}
    first = call(client, "CreatePrintJobUpload", job)["slot"]["fileId"]
    second = call(client, "CreatePrintJobUpload", job)["slot"]["fileId"]

    body = call(client, "GetPrintJob", {"printJobId": id_json(STUB_DRAFT_JOB_ID)})
    assert first != second
    assert body["printJob"]["fileId"] == second


def test_upload_refused_for_a_job_past_draft(client: TestClient) -> None:
    job = {"printJobId": id_json(STUB_SUBMITTED_JOB_ID), "metadata": METADATA}
    body = call(client, "CreatePrintJobUpload", job, expect=400)
    assert body["code"] == "failed_precondition"


@pytest.mark.parametrize(
    "metadata",
    [
        {**METADATA, "fileType": "FILE_TYPE_UNSPECIFIED"},
        {**METADATA, "sizeBytes": "0"},
        {**METADATA, "sha256": "not a hash"},
        {**METADATA, "filename": ""},
    ],
)
def test_upload_rejects_bad_metadata(client: TestClient, metadata: Json) -> None:
    job = {"printJobId": id_json(STUB_DRAFT_JOB_ID), "metadata": metadata}
    body = call(client, "CreatePrintJobUpload", job, expect=400)
    assert body["code"] == "invalid_argument"

    unchanged = call(client, "GetPrintJob", {"printJobId": id_json(STUB_DRAFT_JOB_ID)})
    assert "fileId" not in unchanged["printJob"]


def test_submit_refused_without_an_upload(client: TestClient) -> None:
    body = call(client, "SubmitPrintJob", {"printJobId": id_json(STUB_DRAFT_JOB_ID)}, expect=400)
    assert body["code"] == "failed_precondition"


def test_start_review_refused_by_the_rule(client: TestClient) -> None:
    job = {"printJobId": id_json(STUB_APPROVED_JOB_ID), "startReview": {}}
    assert call(client, "TransitionPrintJob", job, expect=400)["code"] == "failed_precondition"


def test_reject_records_the_reason(client: TestClient) -> None:
    job = {"printJobId": id_json(STUB_SUBMITTED_JOB_ID)}
    call(client, "TransitionPrintJob", {**job, "startReview": {}})

    body = call(client, "TransitionPrintJob", {**job, "reject": {"reason": "Too large"}})

    assert body["printJob"]["status"] == "PRINT_JOB_STATUS_REJECTED"
    assert body["printJob"]["statusReason"] == "Too large"


def test_reject_refused_without_a_reason(client: TestClient) -> None:
    job = {"printJobId": id_json(STUB_SUBMITTED_JOB_ID)}
    call(client, "TransitionPrintJob", {**job, "startReview": {}})

    body = call(client, "TransitionPrintJob", {**job, "reject": {}}, expect=400)
    assert body["code"] == "failed_precondition"


def test_assign_rejects_a_malformed_printer_id(client: TestClient) -> None:
    job = {"printJobId": id_json(STUB_APPROVED_JOB_ID), "assign": {"printerId": {"value": "x"}}}
    body = call(client, "TransitionPrintJob", job, expect=400)
    assert body == {"code": "invalid_argument", "message": "printer_id must be a UUID"}


def test_transition_requires_an_action(client: TestClient) -> None:
    body = call(client, "TransitionPrintJob", {"printJobId": id_json(STUB_APPROVED_JOB_ID)}, 400)
    assert body["code"] == "invalid_argument"


def test_list_pages_through_every_job_with_its_files(client: TestClient) -> None:
    first = call(client, "ListPrintJobs", {"page": {"pageSize": 3}})
    token = first["page"]["nextPageToken"]
    second = call(client, "ListPrintJobs", {"page": {"pageSize": 3, "pageToken": token}})

    ids = [job["id"] for page in (first, second) for job in page["printJobs"]]
    assert ids == [
        id_json(STUB_DRAFT_JOB_ID),
        id_json(STUB_SUBMITTED_JOB_ID),
        id_json(STUB_APPROVED_JOB_ID),
        id_json(STUB_PRINTING_JOB_ID),
        id_json(STUB_FINISHED_JOB_ID),
    ]
    assert {file["id"]["value"] for file in first["files"]} == {
        str(STUB_SUBMITTED_FILE_ID),
        str(STUB_APPROVED_FILE_ID),
    }
    assert "nextPageToken" not in second.get("page", {})


def test_list_rejects_a_bad_page_token(client: TestClient) -> None:
    body = call(client, "ListPrintJobs", {"page": {"pageToken": "nope"}}, expect=400)
    assert body["code"] == "invalid_argument"


def test_staff_fail_a_printing_job_with_a_reason(client: TestClient) -> None:
    job = {"printJobId": id_json(STUB_PRINTING_JOB_ID)}
    body = call(client, "TransitionPrintJob", {**job, "fail": {"reason": "Spaghetti at layer 40"}})

    assert body["printJob"]["status"] == "PRINT_JOB_STATUS_FAILED"
    assert body["printJob"]["statusReason"] == "Spaghetti at layer 40"
