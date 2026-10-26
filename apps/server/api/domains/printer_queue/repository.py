from abc import abstractmethod

from core_domain.ddd import AbstractAsyncRepository, Page
from core_domain.ids import PrinterQueueId
from core_domain.printer_queue import PrinterQueue


class PrinterQueueRepository(AbstractAsyncRepository[PrinterQueueId, PrinterQueue]):
    """Where the server keeps printer queues. The server owns queue state."""

    @abstractmethod
    async def page(self, page_size: int, page_token: str) -> Page[PrinterQueue]:
        """Oldest first. An empty token starts at the first page. Raises InvalidPageToken for a
        token this repository did not issue."""
