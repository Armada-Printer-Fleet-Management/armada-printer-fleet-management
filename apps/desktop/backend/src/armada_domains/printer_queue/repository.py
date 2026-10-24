from abc import abstractmethod

from core_domain.ddd import AbstractReadRepository, Page
from core_domain.ids import PrinterQueueId
from core_domain.printer_queue import PrinterQueue


class PrinterQueueRepository(AbstractReadRepository[PrinterQueueId, PrinterQueue]):
    """Printer queues as the application server keeps them. Implementations live in
    armada_infrastructure."""

    @abstractmethod
    def page(self, page_size: int, page_token: str) -> Page[PrinterQueue]: ...
