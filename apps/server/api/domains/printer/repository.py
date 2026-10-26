from abc import abstractmethod

from core_domain.ddd import AbstractAsyncReadRepository, Page
from core_domain.ids import PrinterId, PrintJobId
from core_domain.printer import Printer


class PrinterRepository(AbstractAsyncReadRepository[PrinterId, Printer]):
    """Where the server reads printer entities from."""

    @abstractmethod
    async def page(self, page_size: int, page_token: str) -> Page[Printer]:
        """An empty token starts at the first page. Raises InvalidPageToken for a token this
        repository did not issue."""

    @abstractmethod
    async def request_dispatch(self, printer_id: PrinterId, print_job_id: PrintJobId) -> Printer:
        """Asks the printer to start the job."""

    @abstractmethod
    async def request_release(self, printer_id: PrinterId) -> Printer:
        """Asks a finished printer to take its next job, once an operator has cleared it."""
