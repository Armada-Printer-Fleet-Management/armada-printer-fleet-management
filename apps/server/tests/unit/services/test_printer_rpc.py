from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient
from proto_utils.gen.server.v1.printer_queue_service_connect import (
    PrinterQueueServiceASGIApplication,
)
from proto_utils.gen.server.v1.printer_service_connect import PrinterServiceASGIApplication

from api.domains.fleet.service import PrinterService
from api.domains.queue.service import PrinterQueueService
from api.infrastructure.dev_data import (
    STUB_FINISHED_PRINTER_ID,
    STUB_IDLE_PRINTER_ID,
    STUB_PRINTER_QUEUE_ID,
    stub_printer_queues,
    stub_printers,
)
from api.infrastructure.printer_queue_memory import InMemoryPrinterQueueRepository
from api.infrastructure.printer_server_mock import MockPrinterServer
from api.services.printer_queue_service import PrinterQueueServiceImplementation
from api.services.printer_service import PrinterServiceImplementation
from tests.rpc import id_json


def test_list_printer_queues_returns_the_open_queue() -> None:
    queues = PrinterQueueService(InMemoryPrinterQueueRepository(stub_printer_queues()))
    client = TestClient(
        PrinterQueueServiceASGIApplication(PrinterQueueServiceImplementation(queues))
    )

    response = client.post("/server.v1.PrinterQueueService/ListPrinterQueues", json={})
    assert response.json()["printerQueues"][0]["id"] == id_json(STUB_PRINTER_QUEUE_ID)


@pytest.fixture
def client() -> TestClient:
    printers = PrinterService(MockPrinterServer(stub_printers(), lambda: datetime.now(UTC)))
    return TestClient(PrinterServiceASGIApplication(PrinterServiceImplementation(printers)))


def ready(client: TestClient, printer_id: object) -> Any:
    body = {"printerId": id_json(printer_id), "ready": {}}
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
