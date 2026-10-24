from abc import abstractmethod

from core_domain.ddd import AbstractReadRepository, Page
from core_domain.ids import PrinterId
from core_domain.printer import Printer


class PrinterRepository(AbstractReadRepository[PrinterId, Printer]):
    """Printers as the application server reports them. A change is requested from it, and the
    printer returned is the result. Implementations live in armada_infrastructure."""

    @abstractmethod
    def page(self, page_size: int, page_token: str) -> Page[Printer]: ...

    @abstractmethod
    def request_ready(self, printer_id: PrinterId) -> Printer: ...
