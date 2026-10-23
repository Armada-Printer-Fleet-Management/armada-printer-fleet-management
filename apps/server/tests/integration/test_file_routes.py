import asyncio
import hashlib
from datetime import UTC, datetime

import pytest
from core_domain.file import FileType
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.common.consts import API_PREFIX
from api.domains.file.service import FileService
from api.infrastructure.file_memory import InMemoryFileRepository
from api.infrastructure.file_store_files import FileStoreFiles
from api.routers.file import file_router, upload_path
from tests.fakes import MemoryFileStore

CONTENT = b"G28\nG1 X10 Y10 F3000\n"
UNKNOWN = f"{API_PREFIX}/files/00000000-0000-4000-8000-0000000000ff"


@pytest.fixture
def store() -> MemoryFileStore:
    return MemoryFileStore()


@pytest.fixture
def service(store: MemoryFileStore) -> FileService:
    storage = FileStoreFiles(lambda: store)
    asyncio.run(storage.__aenter__())
    return FileService(InMemoryFileRepository(), storage, lambda: datetime.now(UTC))


# The app's own file service reaches real storage, so these tests mount the router over fakes.
@pytest.fixture
def client(service: FileService) -> TestClient:
    rest = FastAPI()
    rest.include_router(file_router(service), prefix=API_PREFIX)
    return TestClient(rest)


def new_upload(service: FileService, filename: str = "part.gcode") -> str:
    file = asyncio.run(
        service.create_upload(
            filename, FileType.GCODE, len(CONTENT), hashlib.sha256(CONTENT).hexdigest()
        )
    )
    return upload_path(file.id)


def test_an_uploaded_file_downloads_with_its_name_and_size(
    client: TestClient, service: FileService
) -> None:
    url = new_upload(service, "Part One.gcode")

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
    url = new_upload(service)

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
    url = new_upload(service)
    client.put(url, content=CONTENT)

    assert client.delete(url).status_code == 204
    assert client.get(url).status_code == 404


def test_a_store_outage_is_unavailable_without_its_details(
    client: TestClient, service: FileService, store: MemoryFileStore
) -> None:
    url = new_upload(service)
    store.healthy = False

    response = client.put(url, content=CONTENT)

    assert response.status_code == 503
    assert response.json() == {"detail": "file storage is unavailable"}
