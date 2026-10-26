from connectrpc.request import RequestContext
from core_domain.ids import PrinterQueueId
from proto_utils.gen.common.v1.page_pb2 import PageResponse
from proto_utils.gen.server.v1.printer_queue_service_pb2 import (
    GetPrinterQueueRequest,
    GetPrinterQueueResponse,
    ListPrinterQueuesRequest,
    ListPrinterQueuesResponse,
)
from proto_utils.mappers import PrinterQueueMapper

from api.domains.printer_queue.service import PrinterQueueService
from api.services.domain_errors import domain_errors_as_connect, request_id


class PrinterQueueServiceImplementation:
    """The Connect handler for server.v1.PrinterQueueService."""

    _mapper = PrinterQueueMapper()

    def __init__(self, printer_queues: PrinterQueueService) -> None:
        self._printer_queues = printer_queues

    async def list_printer_queues(
        self,
        request: ListPrinterQueuesRequest,
        ctx: RequestContext[ListPrinterQueuesRequest, ListPrinterQueuesResponse],
        /,
    ) -> ListPrinterQueuesResponse:
        with domain_errors_as_connect():
            page = await self._printer_queues.page(request.page.page_size, request.page.page_token)
        return ListPrinterQueuesResponse(
            printer_queues=[self._mapper.to_proto(queue) for queue in page.items],
            page=PageResponse(next_page_token=page.next_page_token),
        )

    async def get_printer_queue(
        self,
        request: GetPrinterQueueRequest,
        ctx: RequestContext[GetPrinterQueueRequest, GetPrinterQueueResponse],
        /,
    ) -> GetPrinterQueueResponse:
        printer_queue_id = request_id(PrinterQueueId, request.printer_queue_id)
        with domain_errors_as_connect():
            printer_queue = await self._printer_queues.get(printer_queue_id)
        return GetPrinterQueueResponse(printer_queue=self._mapper.to_proto(printer_queue))
