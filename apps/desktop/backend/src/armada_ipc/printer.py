"""Printers, read from and changed on the application server through the printer domain."""

from core_domain.ids import PrinterId
from proto_utils.gen.common.v1.page_pb2 import PageResponse
from proto_utils.gen.server.v1.printer_service_pb2 import (
    ListPrintersRequest,
    ListPrintersResponse,
    TransitionPrinterRequest,
    TransitionPrinterResponse,
)
from proto_utils.mappers import PrinterMapper

from armada_domains.printer.service import PrinterService
from armada_ipc._base import IpcModule, proto_call


class PrinterIpc(IpcModule):
    _mapper = PrinterMapper()

    def __init__(self, printers: PrinterService) -> None:
        self._printers = printers

    @proto_call(ListPrintersRequest)
    def list_printers(self, request: ListPrintersRequest) -> ListPrintersResponse:
        page = self._printers.page(request.page.page_size, request.page.page_token)
        return ListPrintersResponse(
            printers=[self._mapper.to_proto(printer) for printer in page.items],
            page=PageResponse(next_page_token=page.next_page_token),
        )

    @proto_call(TransitionPrinterRequest)
    def transition_printer(self, request: TransitionPrinterRequest) -> TransitionPrinterResponse:
        printer_id = self._mapper.id_from_proto(PrinterId, request.printer_id)
        match request.WhichOneof("action"):
            case "ready":
                printer = self._printers.ready(printer_id)
            case _:
                raise ValueError("action must be set")
        return TransitionPrinterResponse(printer=self._mapper.to_proto(printer))
