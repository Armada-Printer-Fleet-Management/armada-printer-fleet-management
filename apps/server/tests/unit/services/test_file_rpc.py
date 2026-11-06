from collections.abc import Iterable

import pytest
from core_domain.content_asset import File
from core_domain.ddd import Unavailable
from core_domain.ids import FileId
from fastapi.testclient import TestClient

from api.common.consts import API_PREFIX
from api.infrastructure.dev_data import (
    STUB_APPROVED_FILE_ID,
    STUB_STUDENT_ID,
    STUB_SUBMITTED_FILE_ID,
)
from api.infrastructure.file_memory import InMemoryFileRepository
from tests.fake_app import FakeApp, fake_services
from tests.rpc import Json, id_json, post

_RPC = f"{API_PREFIX}/server.v1.FileService"
_UNKNOWN = {"value": "00000000-0000-4000-8000-0000000002ff"}


def test_get_file_returns_the_file(client: TestClient) -> None:
    file = post(client, f"{_RPC}/GetFile", {"fileId": id_json(STUB_SUBMITTED_FILE_ID)})["file"]

    assert file["id"] == id_json(STUB_SUBMITTED_FILE_ID)
    assert file["userId"] == id_json(STUB_STUDENT_ID)
    assert file["filename"] == "stub-submitted.gcode"
    assert file["sizeBytes"] == "1024"
    assert file["fileType"] == "FILE_TYPE_GCODE"


def test_get_file_reports_an_unknown_id(client: TestClient) -> None:
    assert post(client, f"{_RPC}/GetFile", {"fileId": _UNKNOWN}, expect=404)["code"] == "not_found"


def test_list_files_skips_unknown_ids(client: TestClient) -> None:
    ids = [id_json(STUB_SUBMITTED_FILE_ID), _UNKNOWN, id_json(STUB_APPROVED_FILE_ID)]

    files = post(client, f"{_RPC}/ListFiles", {"fileIds": ids})["files"]

    assert sorted(file["id"]["value"] for file in files) == sorted(
        [str(STUB_SUBMITTED_FILE_ID), str(STUB_APPROVED_FILE_ID)]
    )


@pytest.mark.parametrize(
    ("rpc", "body"),
    [("GetFile", {"fileId": {"value": "nope"}}), ("ListFiles", {"fileIds": [{"value": "nope"}]})],
    ids=["get", "list"],
)
def test_a_malformed_id_is_rejected(client: TestClient, rpc: str, body: Json) -> None:
    assert post(client, f"{_RPC}/{rpc}", body, expect=400) == {
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
def test_a_database_outage_is_unavailable_without_its_cause(
    fake_app: FakeApp, rpc: str, body: Json
) -> None:
    client = fake_app(fake_services(files=_UnavailableFiles()))

    assert post(client, f"{_RPC}/{rpc}", body, expect=503) == {
        "code": "unavailable",
        "message": "database is unavailable",
    }
