from core_domain.ddd import Page, Service
from core_domain.ids import PrinterId
from core_domain.printer import Printer

from armada_domains.printer.repository import PrinterRepository


class PrinterService(Service[PrinterRepository]):
    def get(self, printer_id: PrinterId) -> Printer:
        return self._repository.get(printer_id)

    def page(self, page_size: int, page_token: str) -> Page[Printer]:
        return self._repository.page(page_size, page_token)

    def ready(self, printer_id: PrinterId) -> Printer:
        return self._repository.request_ready(printer_id)
