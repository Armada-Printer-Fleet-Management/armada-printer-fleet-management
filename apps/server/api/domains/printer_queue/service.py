from core_domain.ddd import Page, RuleViolation, Service
from core_domain.ids import PrinterQueueId
from core_domain.printer_queue import PrinterQueue

from api.domains.printer_queue.repository import PrinterQueueRepository


class PrinterQueueService(Service[PrinterQueueRepository]):
    async def get(self, printer_queue_id: PrinterQueueId) -> PrinterQueue:
        return await self._repository.get(printer_queue_id)

    async def page(self, page_size: int, page_token: str) -> Page[PrinterQueue]:
        return await self._repository.page(page_size, page_token)

    async def open_queue(self) -> PrinterQueueId:
        """The queue a newly submitted job goes in: the oldest that accepts jobs."""
        page_token = ""
        while True:
            page = await self._repository.page(0, page_token)
            for printer_queue in page.items:
                if printer_queue.can_accept_jobs():
                    return printer_queue.id
            if not page.next_page_token:
                raise RuleViolation("No printer queue is accepting print jobs")
            page_token = page.next_page_token
