from fastapi.testclient import TestClient

from api.common.consts import API_PREFIX
from tests.fakes import MemoryFileStore
from tests.print_jobs import CONTENT, file_url, new_draft, upload_slot

UNKNOWN = f"{API_PREFIX}/files/00000000-0000-4000-8000-0000000000ff"


def test_an_uploaded_file_downloads_with_its_name_and_size(file_client: TestClient) -> None:
    slot = upload_slot(file_client, new_draft(file_client), "Part One.gcode")

    assert file_client.put(slot["uploadUrl"], content=CONTENT).status_code == 204
    response = file_client.get(file_url(slot))

    assert response.status_code == 200
    assert response.content == CONTENT
    assert response.headers["content-type"] == "application/octet-stream"
    assert response.headers["content-length"] == str(len(CONTENT))
    assert response.headers["content-disposition"] == (
        "attachment; filename*=UTF-8''Part%20One.gcode"
    )


def test_an_unknown_file_is_not_found(file_client: TestClient) -> None:
    assert file_client.get(UNKNOWN).status_code == 404


def test_a_malformed_id_is_rejected(file_client: TestClient) -> None:
    assert file_client.get(f"{API_PREFIX}/files/nope").status_code == 422


def test_a_store_outage_after_upload_is_unavailable(
    file_client: TestClient, store: MemoryFileStore
) -> None:
    slot = upload_slot(file_client, new_draft(file_client))
    file_client.put(slot["uploadUrl"], content=CONTENT)
    store.healthy = False

    response = file_client.get(file_url(slot))

    assert response.status_code == 503
    assert "refused" not in response.text
