from collections.abc import Iterable
from datetime import UTC, datetime

import pytest
from core_domain.content_asset import File
from core_domain.ddd import Unavailable
from core_domain.ids import FileId
from fastapi.testclient import TestClient
from proto_utils.gen.server.v1.file_service_connect import FileServiceASGIApplication

from api.domains.content_asset.service import FileService
from api.infrastructure.dev_data import (
    STUB_APPROVED_FILE_ID,
    STUB_STUDENT_ID,
    STUB_SUBMITTED_FILE_ID,
    stub_files,
)
from api.infrastructure.file_memory import InMemoryFileRepository
from api.infrastructure.file_store_files import FileStoreFiles
from api.services.file_service import FileServiceImplementation
from tests.fakes import MemoryFileStore
from tests.rpc import Json, id_json

_RPC = "/server.v1.FileService"
NOW = datetime(2026, 10, 7, 12, 0, tzinfo=UTC)
_UNKNOWN = {"value": "00000000-0000-4000-8000-0000000002ff"}


def _client(repository: InMemoryFileRepository) -> TestClient:
    files = FileService(repository, FileStoreFiles(MemoryFileStore), clock=lambda: NOW)
    return TestClient(FileServiceASGIApplication(FileServiceImplementation(files)))


@pytest.fixture
def client() -> TestClient:
    return _client(InMemoryFileRepository(stub_files()))


def _call(client: TestClient, rpc: str, body: Json, expect: int = 200) -> Json:
    response = client.post(f"{_RPC}/{rpc}", json=body)
    assert response.status_code == expect, response.text
    result: Json = response.json()
    return result


def test_get_file_returns_the_file(client: TestClient) -> None:
    file = _call(client, "GetFile", {"fileId": id_json(STUB_SUBMITTED_FILE_ID)})["file"]

    assert file["id"] == id_json(STUB_SUBMITTED_FILE_ID)
    assert file["userId"] == id_json(STUB_STUDENT_ID)
    assert file["filename"] == "stub-submitted.gcode"
    assert file["sizeBytes"] == "1024"
    assert file["fileType"] == "FILE_TYPE_GCODE"


def test_get_file_reports_an_unknown_id(client: TestClient) -> None:
    assert _call(client, "GetFile", {"fileId": _UNKNOWN}, expect=404)["code"] == "not_found"


def test_list_files_skips_unknown_ids(client: TestClient) -> None:
    ids = [id_json(STUB_SUBMITTED_FILE_ID), _UNKNOWN, id_json(STUB_APPROVED_FILE_ID)]

    files = _call(client, "ListFiles", {"fileIds": ids})["files"]

    assert sorted(file["id"]["value"] for file in files) == sorted(
        [str(STUB_SUBMITTED_FILE_ID), str(STUB_APPROVED_FILE_ID)]
    )


@pytest.mark.parametrize(
    ("rpc", "body"),
    [("GetFile", {"fileId": {"value": "nope"}}), ("ListFiles", {"fileIds": [{"value": "nope"}]})],
    ids=["get", "list"],
)
def test_a_malformed_id_is_rejected(client: TestClient, rpc: str, body: Json) -> None:
    assert _call(client, rpc, body, expect=400) == {
        "code": "invalid_argument",
        "message": "file_id must be a UUID",
    }


class _UnavailableFiles(InMemoryFileRepository):
    async def get(self, entity_id: FileId) -> File:
        raise Unavailable("database") from OSError("db.internal refused the connection")

    async def get_many(self, file_ids: Iterable[FileId]) -> list[File]:
        raise Unavailable("database") from OSError("db.internal refused the connection")


@pytest.mark.parametrize(
    ("rpc", "body"),
    [
        ("GetFile", {"fileId": id_json(STUB_SUBMITTED_FILE_ID)}),
        ("ListFiles", {"fileIds": [id_json(STUB_SUBMITTED_FILE_ID)]}),
    ],
    ids=["get", "list"],
)
def test_a_database_outage_is_unavailable_without_its_cause(rpc: str, body: Json) -> None:
    client = _client(_UnavailableFiles())

    assert _call(client, rpc, body, expect=503) == {
        "code": "unavailable",
        "message": "database is unavailable",
    }
