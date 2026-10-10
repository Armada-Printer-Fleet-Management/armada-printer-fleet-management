from typing import Protocol

from core_domain.ddd import ReadRepository
from core_domain.ids import PrintJobId
from core_domain.print_job import PrintJob


class PrintJobRepository(ReadRepository[PrintJobId, PrintJob], Protocol):
    """A change is requested from the application server, which validates it,
    applies it and returns the result. Implementations live in armada_infrastructure."""

    def request_start_review(self, print_job_id: PrintJobId) -> PrintJob: ...
