"""A print job's file upload route on the running app, with jobs and file records in Postgres
and bytes in Garage."""

from fastapi.testclient import TestClient
from types_boto3_s3.client import S3Client

from api.infrastructure.dev_data import STUB_DRAFT_JOB_ID
from tests.integration.utils.file_store import stored_object_count
from tests.print_jobs import CONTENT, call, file_url, upload_slot
from tests.rpc import id_json

DRAFT = {"printJobId": id_json(STUB_DRAFT_JOB_ID)}


def test_bytes_that_do_not_match_are_refused_and_not_stored(
    app_client: TestClient, file_store_client: S3Client, stack_environment: dict[str, str]
) -> None:
    slot = upload_slot(app_client, STUB_DRAFT_JOB_ID)

    response = app_client.put(slot["uploadUrl"], content=CONTENT.lower())

    assert response.status_code == 400
    assert stored_object_count(file_store_client, stack_environment["FILE_STORE_BUCKET"]) == 0
    assert app_client.get(file_url(slot)).status_code == 404


def test_a_submitted_jobs_file_cannot_be_replaced(
    app_client: TestClient, file_store_client: S3Client, stack_environment: dict[str, str]
) -> None:
    slot = upload_slot(app_client, STUB_DRAFT_JOB_ID)
    app_client.put(slot["uploadUrl"], content=CONTENT)
    call(app_client, "SubmitPrintJob", DRAFT)

    assert app_client.put(slot["uploadUrl"], content=CONTENT).status_code == 409

    assert stored_object_count(file_store_client, stack_environment["FILE_STORE_BUCKET"]) == 1
    assert app_client.get(file_url(slot)).content == CONTENT
