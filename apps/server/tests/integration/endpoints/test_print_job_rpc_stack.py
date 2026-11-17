from fastapi.testclient import TestClient
from types_boto3_s3.client import S3Client

from api.infrastructure.dev_data import (
    STUB_DRAFT_JOB_ID,
    STUB_STUDENT_ID,
    STUB_SUBMITTED_JOB_ID,
)
from tests.integration.utils.file_store import stored_object_count
from tests.print_jobs import (
    CONTENT,
    PRINT_JOB_RPC,
    call,
    file_url,
    upload_slot,
)
from tests.rpc import id_json


def test_rpc_is_mounted_on_the_app(app_client: TestClient) -> None:
    response = app_client.post(
        f"{PRINT_JOB_RPC}/GetPrintJob", json={"printJobId": id_json(STUB_SUBMITTED_JOB_ID)}
    )

    assert response.status_code == 200
    assert response.json()["printJob"]["status"] == "PRINT_JOB_STATUS_SUBMITTED"


def test_a_created_job_reads_back_from_the_database(app_client: TestClient) -> None:
    created = call(app_client, "CreatePrintJob", {"userNotes": "Please use PLA"})

    job = {"printJobId": created["printJob"]["id"]}
    stored = call(app_client, "GetPrintJob", job)["printJob"]

    assert stored["id"] == created["printJob"]["id"]
    assert stored["status"] == "PRINT_JOB_STATUS_DRAFT"
    assert stored["userNotes"] == "Please use PLA"
    assert stored["userId"] == id_json(STUB_STUDENT_ID)


def test_a_job_whose_bytes_are_stored_can_be_submitted(app_client: TestClient) -> None:
    slot = upload_slot(app_client, STUB_DRAFT_JOB_ID)
    assert app_client.put(slot["uploadUrl"], content=CONTENT).status_code == 204

    job = {"printJobId": id_json(STUB_DRAFT_JOB_ID)}
    submitted = call(app_client, "SubmitPrintJob", job)

    assert submitted["printJob"]["status"] == "PRINT_JOB_STATUS_SUBMITTED"
    assert submitted["file"]["id"] == slot["fileId"]


def test_submit_is_refused_while_the_bytes_are_not_stored(app_client: TestClient) -> None:
    upload_slot(app_client, STUB_DRAFT_JOB_ID)

    job = {"printJobId": id_json(STUB_DRAFT_JOB_ID)}
    refused = call(app_client, "SubmitPrintJob", job, expect=400)

    assert refused["code"] == "failed_precondition"
    unchanged = call(app_client, "GetPrintJob", job)["printJob"]
    assert unchanged["status"] == "PRINT_JOB_STATUS_DRAFT"


DRAFT = {"printJobId": id_json(STUB_DRAFT_JOB_ID)}


def test_a_deleted_file_is_gone_with_its_bytes(
    app_client: TestClient, file_store_client: S3Client, stack_environment: dict[str, str]
) -> None:
    slot = upload_slot(app_client, STUB_DRAFT_JOB_ID)
    app_client.put(slot["uploadUrl"], content=CONTENT)
    assert stored_object_count(file_store_client, stack_environment["FILE_STORE_BUCKET"]) == 1

    call(app_client, "DeletePrintJobFile", DRAFT)

    assert app_client.get(file_url(slot)).status_code == 404
    assert stored_object_count(file_store_client, stack_environment["FILE_STORE_BUCKET"]) == 0


def test_delete_leaves_the_stored_draft_without_a_file(app_client: TestClient) -> None:
    slot = upload_slot(app_client, STUB_DRAFT_JOB_ID)
    app_client.put(slot["uploadUrl"], content=CONTENT)

    call(app_client, "DeletePrintJobFile", DRAFT)

    job = call(app_client, "GetPrintJob", DRAFT)["printJob"]
    assert job["status"] == "PRINT_JOB_STATUS_DRAFT"
    assert "fileId" not in job


def test_a_submitted_jobs_file_cannot_be_deleted(
    app_client: TestClient, file_store_client: S3Client, stack_environment: dict[str, str]
) -> None:
    slot = upload_slot(app_client, STUB_DRAFT_JOB_ID)
    app_client.put(slot["uploadUrl"], content=CONTENT)
    call(app_client, "SubmitPrintJob", DRAFT)

    assert (
        call(app_client, "DeletePrintJobFile", DRAFT, expect=400)["code"] == "failed_precondition"
    )

    assert stored_object_count(file_store_client, stack_environment["FILE_STORE_BUCKET"]) == 1
    assert app_client.get(file_url(slot)).content == CONTENT
