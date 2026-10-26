# Stub: keeps printer queues in process memory until the server has a database. Everything is
# lost on restart, and every queue comes back in one page. Replacing it means writing a SQL
# repository for api/domains/printer_queue/repository.py and constructing that in api/main.py.
from collections.abc import Iterable
from dataclasses import replace

from core_domain.ddd import EntityNotFound, InvalidPageToken, Page
from core_domain.ids import PrinterQueueId
from core_domain.printer_queue import PrinterQueue

from api.domains.printer_queue.repository import PrinterQueueRepository


class InMemoryPrinterQueueRepository(PrinterQueueRepository):
    def __init__(self, printer_queues: Iterable[PrinterQueue] = ()) -> None:
        self._printer_queues = {queue.id: queue for queue in printer_queues}

    async def get(self, entity_id: PrinterQueueId) -> PrinterQueue:
        if entity_id not in self._printer_queues:
            raise EntityNotFound(entity_id)
        return replace(self._printer_queues[entity_id])

    async def save(self, entity: PrinterQueue) -> None:
        self._printer_queues[entity.id] = replace(entity)

    async def page(self, page_size: int, page_token: str) -> Page[PrinterQueue]:
        if page_token:
            raise InvalidPageToken()
        oldest_first = sorted(self._printer_queues.values(), key=lambda q: q.created_at)
        return Page([replace(queue) for queue in oldest_first])
