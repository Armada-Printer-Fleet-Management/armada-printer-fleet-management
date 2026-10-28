from functools import cached_property

from core_domain.ddd import Page
from core_domain.ids import PrinterQueueId
from core_domain.printer_queue import PrinterQueue
from proto_utils.gen.common.v1.page_pb2 import PageRequest
from proto_utils.gen.id.v1 import printer_queue_id_pb2
from proto_utils.gen.server.v1.printer_queue_service_connect import PrinterQueueServiceClientSync
from proto_utils.gen.server.v1.printer_queue_service_pb2 import (
    GetPrinterQueueRequest,
    ListPrinterQueuesRequest,
)
from proto_utils.mappers import PrinterQueueMapper

from armada_domains.printer_queue.repository import PrinterQueueRepository
from armada_infrastructure.application_server.client import ApplicationServerClient
from armada_infrastructure.application_server.connection import ApplicationServerConnection


class ApplicationServerPrinterQueues(
    ApplicationServerClient[PrinterQueueId, printer_queue_id_pb2.PrinterQueueId],
    PrinterQueueRepository,
):
    """Reads printer queues from the application server, which owns them."""

    _id_message_type = printer_queue_id_pb2.PrinterQueueId
    _mapper = PrinterQueueMapper()

    def __init__(self, server: ApplicationServerConnection) -> None:
        self._server = server

    @cached_property
    def _client(self) -> PrinterQueueServiceClientSync:
        # Built on first use, so a missing server address fails the call rather than startup.
        return PrinterQueueServiceClientSync(
            self._server.address(), http_client=self._server.http_client
        )

    def get(self, entity_id: PrinterQueueId) -> PrinterQueue:
        request = GetPrinterQueueRequest(printer_queue_id=self._id(entity_id))
        with self._server_errors_as_domain(entity_id):
            response = self._client.get_printer_queue(request)
        return self._mapper.to_entity(response.printer_queue)

    def page(self, page_size: int, page_token: str) -> Page[PrinterQueue]:
        request = ListPrinterQueuesRequest(
            page=PageRequest(page_size=page_size, page_token=page_token)
        )
        with self._server_errors_as_domain():
            response = self._client.list_printer_queues(request)
        return Page(
            [self._mapper.to_entity(queue) for queue in response.printer_queues],
            response.page.next_page_token,
        )
