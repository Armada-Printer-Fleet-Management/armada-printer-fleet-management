from collections.abc import Callable
from datetime import datetime

from core_domain.ddd import Service, change_async
from core_domain.ids import PrintJobId
from core_domain.print_job import PrintJob

from api.domains.print_job.repository import PrintJobRepository


class PrintJobService(Service[PrintJobRepository]):
    def __init__(self, repository: PrintJobRepository, clock: Callable[[], datetime]) -> None:
        super().__init__(repository)
        self._clock = clock

    async def print_job(self, print_job_id: PrintJobId) -> PrintJob:
        return await self._repository.get(print_job_id)

    async def start_review(self, print_job_id: PrintJobId) -> PrintJob:
        now = self._clock()
        return await change_async(
            self._repository, print_job_id, lambda print_job: print_job.start_review(now)
        )
