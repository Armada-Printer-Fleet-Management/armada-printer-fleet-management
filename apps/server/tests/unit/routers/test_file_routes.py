import hashlib

import pytest
from core_domain.content_asset import File, FileType
from core_domain.ids import UserId
from fastapi.testclient import TestClient

from api.common.consts import API_PREFIX
from api.domains.content_asset.service import FileService
from api.infrastructure.file_memory import InMemoryFileRepository
from api.routers.file import upload_path
from tests.fake_app import FakeApp, FakeServices, fake_services, on_app_loop
from tests.fakes import MemoryFileStore

CONTENT = b"G28\nG1 X10 Y10 F3000\n"
UNKNOWN = f"{API_PREFIX}/files/00000000-0000-4000-8000-0000000000ff"


@pytest.fixture
def fakes(store: MemoryFileStore) -> FakeServices:
    return fake_services(files=InMemoryFileRepository(), store=store)


@pytest.fixture
def service(fakes: FakeServices) -> FileService:
    return fakes.services.files


@pytest.fixture
def client(fake_app: FakeApp, fakes: FakeServices) -> TestClient:
    return fake_app(fakes)


def new_upload(client: TestClient, service: FileService, filename: str = "part.gcode") -> str:
    sha256 = hashlib.sha256(CONTENT).hexdigest()

    async def create() -> File:
        return await service.create_upload(
            UserId.new(), filename, FileType.GCODE, len(CONTENT), sha256
        )

    return upload_path(on_app_loop(client, create).id)


def test_an_uploaded_file_downloads_with_its_name_and_size(
    client: TestClient, service: FileService
) -> None:
    url = new_upload(client, service, "Part One.gcode")

    assert client.put(url, content=CONTENT).status_code == 204
    response = client.get(url)

    assert response.status_code == 200
    assert response.content == CONTENT
    assert response.headers["content-type"] == "application/octet-stream"
    assert response.headers["content-length"] == str(len(CONTENT))
    assert response.headers["content-disposition"] == (
        "attachment; filename*=UTF-8''Part%20One.gcode"
    )


def test_bytes_that_do_not_match_are_refused_and_not_stored(
    client: TestClient, service: FileService, store: MemoryFileStore
) -> None:
    url = new_upload(client, service)

    response = client.put(url, content=CONTENT.lower())

    assert response.status_code == 400
    assert store.objects == {}
    assert client.get(url).status_code == 404


@pytest.mark.parametrize("method", ["PUT", "GET", "DELETE"])
def test_an_unknown_file_is_not_found(client: TestClient, method: str) -> None:
    assert client.request(method, UNKNOWN, content=CONTENT).status_code == 404


@pytest.mark.parametrize("method", ["PUT", "GET", "DELETE"])
def test_a_malformed_id_is_rejected(client: TestClient, method: str) -> None:
    assert client.request(method, f"{API_PREFIX}/files/nope").status_code == 422


def test_a_deleted_file_is_gone(client: TestClient, service: FileService) -> None:
    url = new_upload(client, service)
    client.put(url, content=CONTENT)

    assert client.delete(url).status_code == 204
    assert client.get(url).status_code == 404


def test_a_store_outage_is_unavailable_without_its_details(
    client: TestClient, service: FileService, store: MemoryFileStore
) -> None:
    url = new_upload(client, service)
    store.healthy = False

    response = client.put(url, content=CONTENT)

    assert response.status_code == 503
    assert response.json() == {"detail": "file storage is unavailable"}


@pytest.mark.parametrize("method", ["GET", "DELETE"])
def test_a_store_outage_after_upload_is_unavailable(
    client: TestClient, service: FileService, store: MemoryFileStore, method: str
) -> None:
    url = new_upload(client, service)
    client.put(url, content=CONTENT)
    store.healthy = False

    response = client.request(method, url)

    assert response.status_code == 503
    assert "refused" not in response.text
