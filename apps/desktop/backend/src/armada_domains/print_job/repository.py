from abc import abstractmethod

from core_domain.ddd import AbstractReadRepository, Page
from core_domain.ids import PrinterId, PrinterQueueId, PrintJobId
from core_domain.print_job import PrintJob


class PrintJobRepository(AbstractReadRepository[PrintJobId, PrintJob]):
    """A change is requested from the application server, which validates it,
    applies it and returns the result. Implementations live in armada_infrastructure."""

    @abstractmethod
    def page(self, page_size: int, page_token: str) -> Page[PrintJob]: ...

    @abstractmethod
    def request_start_review(self, print_job_id: PrintJobId) -> PrintJob: ...

    @abstractmethod
    def request_approve(self, print_job_id: PrintJobId) -> PrintJob: ...

    @abstractmethod
    def request_reject(self, print_job_id: PrintJobId, reason: str) -> PrintJob: ...

    @abstractmethod
    def request_assign(self, print_job_id: PrintJobId, printer_id: PrinterId) -> PrintJob: ...

    @abstractmethod
    def request_move_to_queue(
        self, print_job_id: PrintJobId, printer_queue_id: PrinterQueueId
    ) -> PrintJob: ...

    @abstractmethod
    def request_complete(self, print_job_id: PrintJobId) -> PrintJob: ...

    @abstractmethod
    def request_fail(self, print_job_id: PrintJobId, reason: str) -> PrintJob: ...
