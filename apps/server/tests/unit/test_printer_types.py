from datetime import UTC, datetime

from fastapi.testclient import TestClient
from proto_utils.gen.server.v1.printer_service_connect import PrinterServiceASGIApplication

from api.domains.fleet.service import PrinterService
from api.infrastructure.dev_data import stub_printers
from api.infrastructure.printer_server_mock import MockPrinterServer
from api.services.printer_service import PrinterServiceImplementation


def test_list_printer_types_returns_each_kind_of_printer_once() -> None:
    printers = PrinterService(MockPrinterServer(stub_printers(), lambda: datetime.now(UTC)))
    handler = PrinterServiceASGIApplication(PrinterServiceImplementation(printers))

    with TestClient(handler) as client:
        response = client.post("/server.v1.PrinterService/ListPrinterTypes", json={})

    assert response.status_code == 200, response.text
    printer_types = response.json()["printerTypes"]
    expected = sorted({printer.printer_type() for printer in stub_printers()})
    assert [each["model"] for each in printer_types] == [each.model for each in expected]
    # A type names no printer and shows no state.
    assert all(set(each) == {"model", "capabilities"} for each in printer_types)
