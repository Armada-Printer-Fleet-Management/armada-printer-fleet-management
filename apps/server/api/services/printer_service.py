from connectrpc.code import Code
from connectrpc.errors import ConnectError
from connectrpc.request import RequestContext
from core_domain.ids import PrinterId
from proto_utils.gen.common.v1.page_pb2 import PageResponse
from proto_utils.gen.server.v1.printer_service_pb2 import (
    GetPrinterRequest,
    GetPrinterResponse,
    ListPrintersRequest,
    ListPrintersResponse,
    TransitionPrinterRequest,
    TransitionPrinterResponse,
)
from proto_utils.mappers import PrinterMapper

from api.domains.printer.service import PrinterService
from api.services.domain_errors import domain_errors_as_connect, request_id


class PrinterServiceImplementation:
    """The Connect handler for server.v1.PrinterService."""

    _mapper = PrinterMapper()

    def __init__(self, printers: PrinterService) -> None:
        self._printers = printers

    async def list_printers(
        self,
        request: ListPrintersRequest,
        ctx: RequestContext[ListPrintersRequest, ListPrintersResponse],
        /,
    ) -> ListPrintersResponse:
        with domain_errors_as_connect():
            page = await self._printers.page(request.page.page_size, request.page.page_token)
        return ListPrintersResponse(
            printers=[self._mapper.to_proto(printer) for printer in page.items],
            page=PageResponse(next_page_token=page.next_page_token),
        )

    async def get_printer(
        self,
        request: GetPrinterRequest,
        ctx: RequestContext[GetPrinterRequest, GetPrinterResponse],
        /,
    ) -> GetPrinterResponse:
        printer_id = request_id(PrinterId, request.printer_id)
        with domain_errors_as_connect():
            printer = await self._printers.get(printer_id)
        return GetPrinterResponse(printer=self._mapper.to_proto(printer))

    async def transition_printer(
        self,
        request: TransitionPrinterRequest,
        ctx: RequestContext[TransitionPrinterRequest, TransitionPrinterResponse],
        /,
    ) -> TransitionPrinterResponse:
        printer_id = request_id(PrinterId, request.printer_id)
        with domain_errors_as_connect():
            match request.WhichOneof("action"):
                case "ready":
                    printer = await self._printers.release(printer_id)
                case _:
                    raise ConnectError(Code.INVALID_ARGUMENT, "action must be set")
        return TransitionPrinterResponse(printer=self._mapper.to_proto(printer))
