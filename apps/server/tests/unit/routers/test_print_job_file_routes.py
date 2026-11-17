from fastapi.testclient import TestClient

from api.common.consts import API_PREFIX
from api.infrastructure.dev_data import STUB_SUBMITTED_JOB_ID
from api.routers.print_job_file import upload_path
from tests.fakes import MemoryFileStore
from tests.print_jobs import CONTENT, file_url, new_draft, upload_slot

UNKNOWN = f"{API_PREFIX}/print-jobs/00000000-0000-4000-8000-0000000000ff/file"
PAST_DRAFT = "A SUBMITTED print job's file cannot be changed"


def test_bytes_that_do_not_match_are_refused_and_not_stored(
    file_client: TestClient, store: MemoryFileStore
) -> None:
    slot = upload_slot(file_client, new_draft(file_client))

    response = file_client.put(slot["uploadUrl"], content=CONTENT.lower())

    assert response.status_code == 400
    assert store.objects == {}
    assert file_client.get(file_url(slot)).status_code == 404


def test_an_unknown_job_is_not_found(file_client: TestClient) -> None:
    assert file_client.put(UNKNOWN, content=CONTENT).status_code == 404


def test_a_malformed_id_is_rejected(file_client: TestClient) -> None:
    response = file_client.put(f"{API_PREFIX}/print-jobs/nope/file")

    assert response.status_code == 422


def test_a_store_outage_is_unavailable_without_its_details(
    file_client: TestClient, store: MemoryFileStore
) -> None:
    slot = upload_slot(file_client, new_draft(file_client))
    store.healthy = False

    response = file_client.put(slot["uploadUrl"], content=CONTENT)

    assert response.status_code == 503
    assert response.json() == {"detail": "file storage is unavailable"}


def test_upload_to_a_job_past_draft_is_refused_and_not_stored(
    file_client: TestClient, store: MemoryFileStore
) -> None:
    response = file_client.put(upload_path(STUB_SUBMITTED_JOB_ID), content=CONTENT)

    assert response.status_code == 409
    assert PAST_DRAFT in response.text
    assert store.objects == {}


def test_a_draft_without_a_file_is_refused(file_client: TestClient) -> None:
    response = file_client.put(upload_path(new_draft(file_client)), content=CONTENT)

    assert response.status_code == 409
    assert "This print job has no file" in response.text
