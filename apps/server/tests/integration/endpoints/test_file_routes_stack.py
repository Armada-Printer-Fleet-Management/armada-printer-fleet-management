"""The file routes on the running app, storing records in Postgres and bytes in Garage."""

from botocore.client import BaseClient
from fastapi.testclient import TestClient

from api.infrastructure.dev_data import STUB_DRAFT_JOB_ID
from tests.print_jobs import CONTENT, METADATA, upload_slot


def _stored_objects(client: BaseClient, environment: dict[str, str]) -> int:
    count: int = client.list_objects_v2(Bucket=environment["FILE_STORE_BUCKET"])["KeyCount"]
    return count


def test_an_uploaded_file_downloads_with_its_name_and_size(app_client: TestClient) -> None:
    url = upload_slot(app_client, STUB_DRAFT_JOB_ID, prefix="/api")["uploadUrl"]

    assert app_client.put(url, content=CONTENT).status_code == 204
    response = app_client.get(url)

    assert response.status_code == 200
    assert response.content == CONTENT
    assert response.headers["content-length"] == str(len(CONTENT))
    assert response.headers["content-disposition"] == (
        f"attachment; filename*=UTF-8''{METADATA['filename']}"
    )


def test_bytes_that_do_not_match_are_refused_and_not_stored(
    app_client: TestClient, file_store_client: BaseClient, stack_environment: dict[str, str]
) -> None:
    url = upload_slot(app_client, STUB_DRAFT_JOB_ID, prefix="/api")["uploadUrl"]

    response = app_client.put(url, content=CONTENT.lower())

    assert response.status_code == 400
    assert _stored_objects(file_store_client, stack_environment) == 0
    assert app_client.get(url).status_code == 404


def test_a_deleted_file_is_gone_with_its_bytes(
    app_client: TestClient, file_store_client: BaseClient, stack_environment: dict[str, str]
) -> None:
    url = upload_slot(app_client, STUB_DRAFT_JOB_ID, prefix="/api")["uploadUrl"]
    app_client.put(url, content=CONTENT)
    assert _stored_objects(file_store_client, stack_environment) == 1

    assert app_client.delete(url).status_code == 204

    assert app_client.get(url).status_code == 404
    assert _stored_objects(file_store_client, stack_environment) == 0
