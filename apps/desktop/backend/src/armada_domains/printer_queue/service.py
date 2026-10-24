from core_domain.ddd import Page, Service
from core_domain.ids import PrinterQueueId
from core_domain.printer_queue import PrinterQueue

from armada_domains.printer_queue.repository import PrinterQueueRepository


class PrinterQueueService(Service[PrinterQueueRepository]):
    def get(self, printer_queue_id: PrinterQueueId) -> PrinterQueue:
        return self._repository.get(printer_queue_id)

    def page(self, page_size: int, page_token: str) -> Page[PrinterQueue]:
        return self._repository.page(page_size, page_token)
