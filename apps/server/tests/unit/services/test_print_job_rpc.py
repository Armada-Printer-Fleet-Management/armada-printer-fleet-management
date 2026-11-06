from datetime import timedelta
from uuid import UUID

import pytest
from core_domain.ddd import Unavailable
from core_domain.ids import FileId, PrinterQueueId, PrintJobId
from core_domain.print_job import PrintJob
from core_domain.queue import PrinterQueue
from fastapi.testclient import TestClient

from api.common.consts import API_PREFIX
from api.infrastructure.dev_data import (
    STUB_APPROVED_FILE_ID,
    STUB_APPROVED_JOB_ID,
    STUB_DRAFT_JOB_ID,
    STUB_FINISHED_JOB_ID,
    STUB_IDLE_PRINTER_ID,
    STUB_PRINTER_QUEUE_ID,
    STUB_PRINTING_JOB_ID,
    STUB_STUDENT_ID,
    STUB_SUBMITTED_FILE_ID,
    STUB_SUBMITTED_JOB_ID,
)
from api.infrastructure.file_memory import InMemoryFileRepository
from api.infrastructure.print_job_memory import InMemoryPrintJobRepository
from api.infrastructure.printer_queue_memory import InMemoryPrinterQueueRepository
from api.infrastructure.printer_server_mock import STEP
from api.routers.file import upload_path
from api.services.printer_poller import PrinterPoller
from tests.fake_app import FakeApp, fake_services, on_app_loop
from tests.print_jobs import (
    CONTENT,
    METADATA,
    PRINT_JOB_RPC,
    call,
    upload_slot,
)
from tests.rpc import Json, id_json
from tests.samples import NOW, printer_queue


def test_get_print_job_returns_the_job_and_its_file(client: TestClient) -> None:
    body = call(client, "GetPrintJob", {"printJobId": id_json(STUB_SUBMITTED_JOB_ID)})

    assert body["printJob"]["id"] == id_json(STUB_SUBMITTED_JOB_ID)
    assert body["file"]["id"] == id_json(STUB_SUBMITTED_FILE_ID)


def test_get_print_job_leaves_file_unset_without_an_upload(client: TestClient) -> None:
    body = call(client, "GetPrintJob", {"printJobId": id_json(STUB_DRAFT_JOB_ID)})
    assert "file" not in body


def test_get_print_job_omits_a_missing_file_record(fake_app: FakeApp) -> None:
    client = fake_app(fake_services(files=InMemoryFileRepository()))
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

    assert response.json()["slot"]["uploadUrl"].startswith(
        f"https://fleet.example.test{API_PREFIX}/files/"
    )


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


_UNKNOWN_JOB = {"value": "00000000-0000-4000-8000-0000000000ff"}
_UNKNOWN_PRINTER = {"value": "00000000-0000-4000-8000-0000000003ff"}
_SECOND_QUEUE_ID = PrinterQueueId(UUID("00000000-0000-4000-8000-000000000402"))


def _client_with_queues(fake_app: FakeApp, *queues: PrinterQueue) -> TestClient:
    return fake_app(fake_services(printer_queues=InMemoryPrinterQueueRepository(queues)))


def test_create_print_job_makes_a_draft_for_the_caller(client: TestClient) -> None:
    created = call(client, "CreatePrintJob", {"userNotes": "Please use PLA"})["printJob"]

    assert created["status"] == "PRINT_JOB_STATUS_DRAFT"
    assert created["userId"] == id_json(STUB_STUDENT_ID)
    assert created["userNotes"] == "Please use PLA"


def test_submit_puts_an_uploaded_job_in_the_open_queue(client: TestClient) -> None:
    slot = upload_slot(client, STUB_DRAFT_JOB_ID)
    assert client.put(slot["uploadUrl"], content=CONTENT).status_code == 204

    body = call(client, "SubmitPrintJob", {"printJobId": id_json(STUB_DRAFT_JOB_ID)})

    assert body["printJob"]["status"] == "PRINT_JOB_STATUS_SUBMITTED"
    assert body["printJob"]["printerQueueId"] == id_json(STUB_PRINTER_QUEUE_ID)
    assert body["file"]["id"] == slot["fileId"]


def test_submit_refused_while_no_queue_accepts_jobs(fake_app: FakeApp) -> None:
    client = _client_with_queues(
        fake_app, printer_queue(is_active=False, printer_queue_id=STUB_PRINTER_QUEUE_ID)
    )
    slot = upload_slot(client, STUB_DRAFT_JOB_ID)
    client.put(slot["uploadUrl"], content=CONTENT)
    job = {"printJobId": id_json(STUB_DRAFT_JOB_ID)}

    body = call(client, "SubmitPrintJob", job, expect=400)

    assert body == {
        "code": "failed_precondition",
        "message": "No printer queue is accepting print jobs",
    }
    assert call(client, "GetPrintJob", job)["printJob"]["status"] == "PRINT_JOB_STATUS_DRAFT"


@pytest.mark.parametrize(
    ("rpc", "body"),
    [
        ("CreatePrintJobUpload", {"printJobId": _UNKNOWN_JOB, "metadata": METADATA}),
        ("SubmitPrintJob", {"printJobId": _UNKNOWN_JOB}),
        ("TransitionPrintJob", {"printJobId": _UNKNOWN_JOB, "approve": {}}),
    ],
    ids=["upload", "submit", "transition"],
)
def test_an_unknown_job_is_not_found(client: TestClient, rpc: str, body: Json) -> None:
    assert call(client, rpc, body, expect=404)["code"] == "not_found"


def test_approve_a_job_under_review(client: TestClient) -> None:
    job = {"printJobId": id_json(STUB_SUBMITTED_JOB_ID)}
    call(client, "TransitionPrintJob", {**job, "startReview": {}})

    body = call(client, "TransitionPrintJob", {**job, "approve": {}})

    assert body["printJob"]["status"] == "PRINT_JOB_STATUS_APPROVED"


def test_assign_an_approved_job_to_an_idle_printer(client: TestClient) -> None:
    printer = id_json(STUB_IDLE_PRINTER_ID)
    job = {"printJobId": id_json(STUB_APPROVED_JOB_ID), "assign": {"printerId": printer}}

    body = call(client, "TransitionPrintJob", job)

    assert body["printJob"]["status"] == "PRINT_JOB_STATUS_ASSIGNED"
    assert body["printJob"]["printerId"] == printer


def test_complete_refused_for_a_job_still_printing(client: TestClient) -> None:
    job = {"printJobId": id_json(STUB_PRINTING_JOB_ID), "complete": {}}
    assert call(client, "TransitionPrintJob", job, expect=400)["code"] == "failed_precondition"


def test_complete_a_finished_job(client: TestClient) -> None:
    job = {"printJobId": id_json(STUB_FINISHED_JOB_ID), "complete": {}}

    body = call(client, "TransitionPrintJob", job)

    assert body["printJob"]["status"] == "PRINT_JOB_STATUS_COMPLETED"


def test_move_to_queue_changes_the_jobs_queue(fake_app: FakeApp) -> None:
    client = _client_with_queues(
        fake_app,
        printer_queue(is_active=True, printer_queue_id=STUB_PRINTER_QUEUE_ID),
        printer_queue(is_active=True, printer_queue_id=_SECOND_QUEUE_ID),
    )
    second = id_json(_SECOND_QUEUE_ID)
    job = {"printJobId": id_json(STUB_APPROVED_JOB_ID), "moveToQueue": {"printerQueueId": second}}

    body = call(client, "TransitionPrintJob", job)

    assert body["printJob"]["printerQueueId"] == second


def test_upload_requires_a_host_header(client: TestClient) -> None:
    response = client.post(
        f"{PRINT_JOB_RPC}/CreatePrintJobUpload",
        json={"printJobId": id_json(STUB_DRAFT_JOB_ID), "metadata": METADATA},
        headers={"Host": ""},
    )

    assert response.status_code == 400
    assert response.json() == {"code": "invalid_argument", "message": "the Host header is required"}


def test_assign_to_an_unknown_printer_is_not_found(client: TestClient) -> None:
    job = {"printJobId": id_json(STUB_APPROVED_JOB_ID), "assign": {"printerId": _UNKNOWN_PRINTER}}
    assert call(client, "TransitionPrintJob", job, expect=404)["code"] == "not_found"


def test_fail_refused_without_a_reason(client: TestClient) -> None:
    job = {"printJobId": id_json(STUB_PRINTING_JOB_ID), "fail": {}}
    assert call(client, "TransitionPrintJob", job, expect=400)["code"] == "failed_precondition"


class _UnavailablePrintJobs(InMemoryPrintJobRepository):
    async def get(self, entity_id: PrintJobId) -> PrintJob:
        raise Unavailable("database") from OSError("db.internal refused the connection")


def test_a_database_outage_is_unavailable_without_its_cause(fake_app: FakeApp) -> None:
    client = fake_app(fake_services(print_jobs=_UnavailablePrintJobs()))

    body = call(client, "GetPrintJob", {"printJobId": id_json(STUB_DRAFT_JOB_ID)}, expect=503)

    assert body == {"code": "unavailable", "message": "database is unavailable"}


def test_a_job_goes_from_creation_to_completed(fake_app: FakeApp) -> None:
    now = [NOW]
    fakes = fake_services(clock=lambda: now[0])
    client = fake_app(fakes)
    poller = PrinterPoller(fakes.services.printers, fakes.services.print_jobs, timedelta(seconds=1))
    created = call(client, "CreatePrintJob", {"userNotes": "Please use PLA"})["printJob"]
    assert created["status"] == "PRINT_JOB_STATUS_DRAFT"
    assert created["userId"] == id_json(STUB_STUDENT_ID)
    job = {"printJobId": created["id"]}

    slot = call(client, "CreatePrintJobUpload", {**job, "metadata": METADATA})["slot"]
    file_path = upload_path(FileId(UUID(slot["fileId"]["value"])))
    assert slot["uploadUrl"] == f"http://testserver{file_path}"
    assert client.put(slot["uploadUrl"], content=CONTENT).status_code == 204

    submitted = call(client, "SubmitPrintJob", job)
    assert submitted["printJob"]["status"] == "PRINT_JOB_STATUS_SUBMITTED"
    assert submitted["printJob"]["printerQueueId"] == id_json(STUB_PRINTER_QUEUE_ID)
    assert submitted["file"]["id"] == slot["fileId"]

    call(client, "TransitionPrintJob", {**job, "startReview": {}})
    call(client, "TransitionPrintJob", {**job, "approve": {}})
    printer = id_json(STUB_IDLE_PRINTER_ID)
    assigned = call(client, "TransitionPrintJob", {**job, "assign": {"printerId": printer}})
    assert assigned["printJob"]["status"] == "PRINT_JOB_STATUS_ASSIGNED"
    assert assigned["printJob"]["printerId"] == printer

    on_app_loop(client, poller.poll)
    assert call(client, "GetPrintJob", job)["printJob"]["status"] == "PRINT_JOB_STATUS_PRINTING"
    refused = call(client, "TransitionPrintJob", {**job, "complete": {}}, expect=400)
    assert refused["code"] == "failed_precondition"

    now[0] += STEP * 4
    on_app_loop(client, poller.poll)
    assert call(client, "GetPrintJob", job)["printJob"]["status"] == "PRINT_JOB_STATUS_FINISHED"
    completed = call(client, "TransitionPrintJob", {**job, "complete": {}})
    assert completed["printJob"]["status"] == "PRINT_JOB_STATUS_COMPLETED"
