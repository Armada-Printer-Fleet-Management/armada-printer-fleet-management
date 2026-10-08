from typing import Protocol

from core_domain.ddd import ReadRepository
from core_domain.ids import PrintJobId
from core_domain.print_job import PrintJob


class PrintJobRepository(ReadRepository[PrintJobId, PrintJob], Protocol):
    """Read-only, so a change made to a print job on the desktop can never be persisted.
    Implementations live in armada_infrastructure."""
