import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from core_domain.ddd import Page, RuleViolation
from core_domain.ids import PrinterQueueId
from core_domain.queue import PrinterQueue

from api.domains.queue.repository import PrinterQueueRepository
from api.domains.queue.service import PrinterQueueService
from api.infrastructure.printer_queue_memory import InMemoryPrinterQueueRepository

START = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)


def queue(is_active: bool, minutes: int = 0) -> PrinterQueue:
    created = START + timedelta(minutes=minutes)
    return PrinterQueue(PrinterQueueId(uuid4()), "Queue", is_active, created, created)


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


def open_queue(repository: PrinterQueueRepository) -> PrinterQueueId:
    return asyncio.run(PrinterQueueService(repository).open_queue())


def test_the_first_queue_accepting_jobs_is_chosen() -> None:
    inactive, active = queue(is_active=False), queue(is_active=True)

    assert open_queue(PagedQueues([inactive, active])) == active.id


def test_a_queue_on_a_later_page_is_found() -> None:
    active = queue(is_active=True)

    assert open_queue(PagedQueues([queue(is_active=False)], [active])) == active.id


def test_no_queue_accepting_jobs_is_refused() -> None:
    with pytest.raises(RuleViolation):
        open_queue(PagedQueues([queue(is_active=False)], [queue(is_active=False)]))


def test_the_oldest_accepting_queue_wins() -> None:
    older, newer = queue(is_active=True, minutes=0), queue(is_active=True, minutes=5)

    assert open_queue(InMemoryPrinterQueueRepository([newer, older])) == older.id
