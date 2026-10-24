"""Printer queues, read from the application server through the printer_queue domain."""

from proto_utils.gen.common.v1.page_pb2 import PageResponse
from proto_utils.gen.server.v1.printer_queue_service_pb2 import (
    ListPrinterQueuesRequest,
    ListPrinterQueuesResponse,
)
from proto_utils.mappers import PrinterQueueMapper

from armada_domains.printer_queue.service import PrinterQueueService
from armada_ipc._base import IpcModule, proto_call


class PrinterQueueIpc(IpcModule):
    _mapper = PrinterQueueMapper()

    def __init__(self, printer_queues: PrinterQueueService) -> None:
        self._printer_queues = printer_queues

    @proto_call(ListPrinterQueuesRequest)
    def list_printer_queues(self, request: ListPrinterQueuesRequest) -> ListPrinterQueuesResponse:
        page = self._printer_queues.page(request.page.page_size, request.page.page_token)
        return ListPrinterQueuesResponse(
            printer_queues=[self._mapper.to_proto(queue) for queue in page.items],
            page=PageResponse(next_page_token=page.next_page_token),
        )
