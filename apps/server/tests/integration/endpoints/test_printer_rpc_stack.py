import pytest
from fastapi.testclient import TestClient

from api.infrastructure.dev_data import STUB_SUBMITTED_FILE_ID
from tests.rpc import Json, id_json


@pytest.mark.parametrize(
    ("rpc", "body", "field"),
    [
        ("server.v1.PrinterService/ListPrinters", {}, "printers"),
        ("server.v1.PrinterQueueService/ListPrinterQueues", {}, "printerQueues"),
        (
            "server.v1.FileService/ListFiles",
            {"fileIds": [id_json(STUB_SUBMITTED_FILE_ID)]},
            "files",
        ),
    ],
)
def test_rpc_is_mounted_on_the_app(
    app_client: TestClient, rpc: str, body: Json, field: str
) -> None:
    response = app_client.post(f"/api/{rpc}", json=body)

    assert response.status_code == 200, response.text
    assert response.json()[field]
