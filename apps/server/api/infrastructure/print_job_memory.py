# Keeps print jobs in process memory, for tests that need a PrintJobRepository without Postgres.
# The server uses SqlPrintJobRepository; both pass tests/contract/test_print_job_repository.py.
from collections.abc import Iterable
from dataclasses import replace

from core_domain.ddd import EntityNotFound, Page
from core_domain.ids import PrintJobId
from core_domain.print_job import PrintJob

from api.domains.print_job.repository import PrintJobRepository
from api.infrastructure.page import newest_first_page


class InMemoryPrintJobRepository(PrintJobRepository):
    def __init__(self, print_jobs: Iterable[PrintJob] = ()) -> None:
        self._print_jobs = {print_job.id: print_job for print_job in print_jobs}

    async def get(self, entity_id: PrintJobId) -> PrintJob:
        if entity_id not in self._print_jobs:
            raise EntityNotFound(entity_id)
        # A copy, as a database would return, so a change is only stored once it is saved.
        return replace(self._print_jobs[entity_id])

    async def save(self, entity: PrintJob) -> None:
        self._print_jobs[entity.id] = replace(entity)

    async def page(self, page_size: int, page_token: str) -> Page[PrintJob]:
        page = newest_first_page(self._print_jobs.values(), page_size, page_token)
        return Page([replace(job) for job in page.items], page.next_page_token)
