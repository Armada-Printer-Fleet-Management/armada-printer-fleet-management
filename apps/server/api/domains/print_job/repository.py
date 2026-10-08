from typing import Protocol

from core_domain.ddd import AsyncRepository
from core_domain.ids import PrintJobId
from core_domain.print_job import PrintJob


class PrintJobRepository(AsyncRepository[PrintJobId, PrintJob], Protocol):
    """Where the server keeps print jobs. Implementations live in api/infrastructure."""
