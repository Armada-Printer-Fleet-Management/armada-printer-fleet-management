import asyncio

from core_domain.ddd import Page, Service, Unavailable
from core_domain.fleet import Printer, PrinterType, printer_types
from core_domain.ids import PrinterId, PrintJobId

from api.domains.fleet.repository import PrinterRepository

_PAGE_SIZE = 100
# Bounds on reading the whole fleet, so a repository that keeps returning pages, or answers
# slowly, cannot hold the request open: 50 pages is 5,000 printers.
_MAX_PAGES = 50
_TIMEOUT_S = 10.0


class PrinterService(Service[PrinterRepository]):
    async def get(self, printer_id: PrinterId) -> Printer:
        return await self._repository.get(printer_id)

    async def page(self, page_size: int, page_token: str) -> Page[Printer]:
        return await self._repository.page(page_size, page_token)

    async def types(self) -> list[PrinterType]:
        """The distinct kinds of printer in the fleet, which is all a student may learn of it.
        Raises Unavailable when the fleet cannot be read within the page and time bounds."""
        printers: list[Printer] = []
        token = ""
        try:
            async with asyncio.timeout(_TIMEOUT_S):
                for _ in range(_MAX_PAGES):
                    page = await self._repository.page(_PAGE_SIZE, token)
                    printers.extend(page.items)
                    if not page.next_page_token:
                        return printer_types(printers)
                    token = page.next_page_token
        except TimeoutError as error:
            raise Unavailable("the printer fleet") from error
        raise Unavailable("the printer fleet")

    async def dispatch(self, printer_id: PrinterId, print_job_id: PrintJobId) -> Printer:
        return await self._repository.request_dispatch(printer_id, print_job_id)

    async def release(self, printer_id: PrinterId) -> Printer:
        return await self._repository.request_release(printer_id)
