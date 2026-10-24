from core_domain.ddd import Page
from core_domain.ids import PrinterId
from core_domain.printer import Printer
from proto_utils.gen.common.v1.page_pb2 import PageRequest
from proto_utils.gen.id.v1 import printer_id_pb2
from proto_utils.gen.server.v1.printer_service_connect import PrinterServiceClientSync
from proto_utils.gen.server.v1.printer_service_pb2 import (
    GetPrinterRequest,
    ListPrintersRequest,
    TransitionPrinterRequest,
)
from proto_utils.mappers import PrinterMapper

from armada_domains.printer.repository import PrinterRepository
from armada_infrastructure.application_server.client import ApplicationServerClient
from armada_infrastructure.application_server.connection import ApplicationServerConnection


class ApplicationServerPrinters(
    ApplicationServerClient[PrinterId, printer_id_pb2.PrinterId], PrinterRepository
):
    """Reads printers from the application server and asks it for changes."""

    _id_message_type = printer_id_pb2.PrinterId
    _mapper = PrinterMapper()

    def __init__(self, server: ApplicationServerConnection) -> None:
        self._client = PrinterServiceClientSync(server.address, http_client=server.http_client)

    def get(self, entity_id: PrinterId) -> Printer:
        request = GetPrinterRequest(printer_id=self._id(entity_id))
        with self._server_errors_as_domain(entity_id):
            response = self._client.get_printer(request)
        return self._mapper.to_entity(response.printer)

    def page(self, page_size: int, page_token: str) -> Page[Printer]:
        request = ListPrintersRequest(page=PageRequest(page_size=page_size, page_token=page_token))
        with self._server_errors_as_domain():
            response = self._client.list_printers(request)
        return Page(
            [self._mapper.to_entity(printer) for printer in response.printers],
            response.page.next_page_token,
        )

    def request_ready(self, printer_id: PrinterId) -> Printer:
        request = TransitionPrinterRequest(
            printer_id=self._id(printer_id), ready=TransitionPrinterRequest.Ready()
        )
        with self._server_errors_as_domain(printer_id):
            response = self._client.transition_printer(request)
        return self._mapper.to_entity(response.printer)
