from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient
from proto_utils.gen.server.v1.printer_service_connect import PrinterServiceASGIApplication

from api.domains.printer.service import PrinterService
from api.infrastructure.printer_server_mock import MockPrinterServer
from api.infrastructure.stub_data import (
    STUB_FINISHED_PRINTER_ID,
    STUB_IDLE_PRINTER_ID,
    STUB_PRINTER_QUEUE_ID,
    STUB_SUBMITTED_FILE_ID,
    stub_printers,
)
from api.main import app
from api.services.printer_service import PrinterServiceImplementation

type Json = dict[str, Any]


def _id(entity_id: object) -> dict[str, str]:
    return {"value": str(entity_id)}


@pytest.mark.parametrize(
    ("rpc", "body", "field"),
    [
        ("server.v1.PrinterService/ListPrinters", {}, "printers"),
        ("server.v1.PrinterQueueService/ListPrinterQueues", {}, "printerQueues"),
        ("server.v1.FileService/ListFiles", {"fileIds": [_id(STUB_SUBMITTED_FILE_ID)]}, "files"),
    ],
)
def test_rpc_is_mounted_on_the_app(rpc: str, body: Json, field: str) -> None:
    response = TestClient(app).post(f"/api/{rpc}", json=body)

    assert response.status_code == 200, response.text
    assert response.json()[field]


def test_list_printer_queues_returns_the_open_queue() -> None:
    response = TestClient(app).post("/api/server.v1.PrinterQueueService/ListPrinterQueues", json={})
    assert response.json()["printerQueues"][0]["id"] == _id(STUB_PRINTER_QUEUE_ID)


@pytest.fixture
def client() -> TestClient:
    printers = PrinterService(MockPrinterServer(stub_printers(), lambda: datetime.now(UTC)))
    return TestClient(PrinterServiceASGIApplication(PrinterServiceImplementation(printers)))


def ready(client: TestClient, printer_id: object) -> Any:
    body = {"printerId": _id(printer_id), "ready": {}}
    return client.post("/server.v1.PrinterService/TransitionPrinter", json=body)


def test_ready_frees_a_finished_printer(client: TestClient) -> None:
    response = ready(client, STUB_FINISHED_PRINTER_ID)

    assert response.status_code == 200, response.text
    printer = response.json()["printer"]
    assert printer["status"] == "PRINTER_STATUS_IDLE"
    assert "printJobId" not in printer


def test_ready_refused_for_a_printer_that_has_not_finished(client: TestClient) -> None:
    response = ready(client, STUB_IDLE_PRINTER_ID)
    assert response.status_code == 400
    assert response.json()["code"] == "failed_precondition"
