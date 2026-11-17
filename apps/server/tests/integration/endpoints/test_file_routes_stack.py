"""The file routes on the running app, storing records in Postgres and bytes in Garage."""

from fastapi.testclient import TestClient

from api.infrastructure.dev_data import STUB_DRAFT_JOB_ID
from tests.print_jobs import CONTENT, METADATA, file_url, upload_slot


def test_an_uploaded_file_downloads_with_its_name_and_size(app_client: TestClient) -> None:
    slot = upload_slot(app_client, STUB_DRAFT_JOB_ID)

    assert app_client.put(slot["uploadUrl"], content=CONTENT).status_code == 204
    response = app_client.get(file_url(slot))

    assert response.status_code == 200
    assert response.content == CONTENT
    assert response.headers["content-length"] == str(len(CONTENT))
    assert response.headers["content-disposition"] == (
        f"attachment; filename*=UTF-8''{METADATA['filename']}"
    )
