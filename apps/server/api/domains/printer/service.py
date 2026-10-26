from core_domain.ddd import Page, Service
from core_domain.ids import PrinterId, PrintJobId
from core_domain.printer import Printer

from api.domains.printer.repository import PrinterRepository


class PrinterService(Service[PrinterRepository]):
    async def get(self, printer_id: PrinterId) -> Printer:
        return await self._repository.get(printer_id)

    async def page(self, page_size: int, page_token: str) -> Page[Printer]:
        return await self._repository.page(page_size, page_token)

    async def dispatch(self, printer_id: PrinterId, print_job_id: PrintJobId) -> Printer:
        return await self._repository.request_dispatch(printer_id, print_job_id)

    async def release(self, printer_id: PrinterId) -> Printer:
        return await self._repository.request_release(printer_id)
