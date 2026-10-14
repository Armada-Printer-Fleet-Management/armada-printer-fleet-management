from typing import Protocol

from core_domain.ddd import AsyncRepository, Page
from core_domain.ids import PrintJobId
from core_domain.print_job import PrintJob


class PrintJobRepository(AsyncRepository[PrintJobId, PrintJob], Protocol):
    """Where the server keeps print jobs. Implementations live in api/infrastructure, and each
    must pass tests/contract/test_print_job_repository.py. A save must not silently overwrite a
    change saved by another request since this one loaded the job."""

    async def page(self, page_size: int, page_token: str) -> Page[PrintJob]:
        """Newest first. An empty token starts at the first page. Raises InvalidPageToken for a
        token this repository did not issue."""
        ...
