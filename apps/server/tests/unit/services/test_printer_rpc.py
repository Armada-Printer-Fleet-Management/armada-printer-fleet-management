from typing import Any

from core_domain.ddd import Unavailable
from core_domain.fleet import Printer
from core_domain.ids import PrinterId, PrinterQueueId
from core_domain.queue import PrinterQueue
from fastapi.testclient import TestClient

from api.infrastructure.dev_data import (
    STUB_FINISHED_PRINTER_ID,
    STUB_IDLE_PRINTER_ID,
    STUB_PRINTER_QUEUE_ID,
    stub_printers,
)
from api.infrastructure.printer_queue_memory import InMemoryPrinterQueueRepository
from api.infrastructure.printer_server_mock import MockPrinterServer
from tests.fake_app import FakeApp, fake_services
from tests.rpc import id_json, post
from tests.samples import NOW


def test_list_printer_queues_returns_the_open_queue(client: TestClient) -> None:
    response = client.post("/api/server.v1.PrinterQueueService/ListPrinterQueues", json={})
    assert response.json()["printerQueues"][0]["id"] == id_json(STUB_PRINTER_QUEUE_ID)


def ready(client: TestClient, printer_id: object) -> Any:
    body = {"printerId": id_json(printer_id), "ready": {}}
    return client.post("/api/server.v1.PrinterService/TransitionPrinter", json=body)


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


_PRINTERS = "/api/server.v1.PrinterService"
_QUEUES = "/api/server.v1.PrinterQueueService"
_UNKNOWN_PRINTER = {"value": "00000000-0000-4000-8000-0000000003ff"}
_UNKNOWN_QUEUE = {"value": "00000000-0000-4000-8000-0000000004ff"}


def test_get_printer_returns_the_printer(client: TestClient) -> None:
    body = post(client, f"{_PRINTERS}/GetPrinter", {"printerId": id_json(STUB_IDLE_PRINTER_ID)})

    assert body["printer"]["id"] == id_json(STUB_IDLE_PRINTER_ID)
    assert body["printer"]["name"] == "Stub printer 1"


def test_get_printer_reports_an_unknown_id(client: TestClient) -> None:
    body = post(client, f"{_PRINTERS}/GetPrinter", {"printerId": _UNKNOWN_PRINTER}, 404)
    assert body["code"] == "not_found"


def test_transition_printer_requires_an_action(client: TestClient) -> None:
    body = {"printerId": id_json(STUB_FINISHED_PRINTER_ID)}

    assert post(client, f"{_PRINTERS}/TransitionPrinter", body, 400) == {
        "code": "invalid_argument",
        "message": "action must be set",
    }


def test_transition_of_an_unknown_printer_is_not_found(client: TestClient) -> None:
    body = {"printerId": _UNKNOWN_PRINTER, "ready": {}}
    assert post(client, f"{_PRINTERS}/TransitionPrinter", body, 404)["code"] == "not_found"


def test_list_printers_returns_every_printer_by_name(client: TestClient) -> None:
    printers = post(client, f"{_PRINTERS}/ListPrinters", {})["printers"]

    assert [printer["name"] for printer in printers] == sorted(
        printer.name for printer in stub_printers()
    )


def test_list_printers_rejects_a_page_token(client: TestClient) -> None:
    body = post(client, f"{_PRINTERS}/ListPrinters", {"page": {"pageToken": "nope"}}, 400)
    assert body["code"] == "invalid_argument"


def test_get_printer_queue_returns_the_queue(client: TestClient) -> None:
    body = {"printerQueueId": id_json(STUB_PRINTER_QUEUE_ID)}

    queue = post(client, f"{_QUEUES}/GetPrinterQueue", body)["printerQueue"]

    assert queue["id"] == id_json(STUB_PRINTER_QUEUE_ID)
    assert queue["name"] == "General"


def test_get_printer_queue_reports_an_unknown_id(client: TestClient) -> None:
    body = {"printerQueueId": _UNKNOWN_QUEUE}
    assert post(client, f"{_QUEUES}/GetPrinterQueue", body, 404)["code"] == "not_found"


class _UnreachablePrinterServer(MockPrinterServer):
    async def get(self, entity_id: PrinterId) -> Printer:
        raise Unavailable("printer server") from OSError("printers.internal refused")


def test_a_printer_server_outage_is_unavailable_without_its_cause(fake_app: FakeApp) -> None:
    server = _UnreachablePrinterServer(stub_printers(), lambda: NOW)
    client = fake_app(fake_services(printer_server=server))

    body = post(
        client, f"{_PRINTERS}/GetPrinter", {"printerId": id_json(STUB_IDLE_PRINTER_ID)}, 503
    )

    assert body == {"code": "unavailable", "message": "printer server is unavailable"}


class _UnavailableQueues(InMemoryPrinterQueueRepository):
    async def get(self, entity_id: PrinterQueueId) -> PrinterQueue:
        raise Unavailable("database") from OSError("db.internal refused the connection")


def test_a_queue_store_outage_is_unavailable_without_its_cause(fake_app: FakeApp) -> None:
    client = fake_app(fake_services(printer_queues=_UnavailableQueues()))
    body = {"printerQueueId": id_json(STUB_PRINTER_QUEUE_ID)}

    assert post(client, f"{_QUEUES}/GetPrinterQueue", body, 503) == {
        "code": "unavailable",
        "message": "database is unavailable",
    }
