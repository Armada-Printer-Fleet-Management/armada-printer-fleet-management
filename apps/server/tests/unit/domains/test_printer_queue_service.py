import pytest
from core_domain.ddd import Page, RuleViolation
from core_domain.ids import PrinterQueueId
from core_domain.queue import PrinterQueue

from api.domains.queue.repository import PrinterQueueRepository
from api.domains.queue.service import PrinterQueueService
from api.infrastructure.printer_queue_memory import InMemoryPrinterQueueRepository
from tests.samples import printer_queue


class PagedQueues(PrinterQueueRepository):
    """Serves fixed pages, each token naming the next page's index, so a test can spread queues
    over more than one page."""

    def __init__(self, *pages: list[PrinterQueue]) -> None:
        self._pages = pages

    async def get(self, entity_id: PrinterQueueId) -> PrinterQueue:
        raise NotImplementedError

    async def save(self, entity: PrinterQueue) -> None:
        raise NotImplementedError

    async def page(self, page_size: int, page_token: str) -> Page[PrinterQueue]:
        index = int(page_token or 0)
        last = index == len(self._pages) - 1
        return Page(self._pages[index], "" if last else str(index + 1))


async def open_queue(repository: PrinterQueueRepository) -> PrinterQueueId:
    return await PrinterQueueService(repository).open_queue()


async def test_the_first_queue_accepting_jobs_is_chosen() -> None:
    inactive, active = printer_queue(is_active=False), printer_queue(is_active=True)

    assert await open_queue(PagedQueues([inactive, active])) == active.id


async def test_a_queue_on_a_later_page_is_found() -> None:
    active = printer_queue(is_active=True)

    assert await open_queue(PagedQueues([printer_queue(is_active=False)], [active])) == active.id


async def test_no_queue_accepting_jobs_is_refused() -> None:
    with pytest.raises(RuleViolation):
        await open_queue(
            PagedQueues([printer_queue(is_active=False)], [printer_queue(is_active=False)])
        )


async def test_the_oldest_accepting_queue_wins() -> None:
    older, newer = (
        printer_queue(is_active=True, minutes=0),
        printer_queue(is_active=True, minutes=5),
    )

    assert await open_queue(InMemoryPrinterQueueRepository([newer, older])) == older.id
