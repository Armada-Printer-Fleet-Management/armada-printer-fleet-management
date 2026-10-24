from collections.abc import Awaitable, Callable
from datetime import datetime

from core_domain.ddd import Page, Service, change_async
from core_domain.ids import FileId, PrinterId, PrintJobId, UserId
from core_domain.print_job import PrintJob

from api.domains.print_job.repository import PrintJobRepository

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100


class PrintJobService(Service[PrintJobRepository]):
    def __init__(self, repository: PrintJobRepository, clock: Callable[[], datetime]) -> None:
        super().__init__(repository)
        self._clock = clock

    async def print_job(self, print_job_id: PrintJobId) -> PrintJob:
        return await self._repository.get(print_job_id)

    async def page(self, page_size: int, page_token: str) -> Page[PrintJob]:
        size = min(page_size, MAX_PAGE_SIZE) if page_size > 0 else DEFAULT_PAGE_SIZE
        return await self._repository.page(size, page_token)

    async def create(self, user_id: UserId, user_notes: str) -> PrintJob:
        print_job = PrintJob.create(user_id, user_notes, self._clock())
        await self._repository.save(print_job)
        return print_job

    async def attach_new_file(
        self, print_job_id: PrintJobId, new_file: Callable[[], Awaitable[FileId]]
    ) -> PrintJob:
        """Attaches the file new_file creates. It is called only once the job is known to accept
        a file, so a refused job leaves no file behind."""
        now = self._clock()

        async def rule(print_job: PrintJob) -> None:
            print_job.require_can_attach_file()
            print_job.attach_file(await new_file(), now)

        return await change_async(self._repository, print_job_id, rule)

    async def submit(
        self, print_job_id: PrintJobId, is_uploaded: Callable[[FileId], Awaitable[bool]]
    ) -> PrintJob:
        """Submits the job, checking the upload of the file on the same copy that is saved."""
        now = self._clock()

        async def rule(print_job: PrintJob) -> None:
            file_id = print_job.file_id
            uploaded = file_id is not None and await is_uploaded(file_id)
            print_job.submit(uploaded, now)

        return await change_async(self._repository, print_job_id, rule)

    async def start_review(self, print_job_id: PrintJobId) -> PrintJob:
        now = self._clock()
        return await change_async(
            self._repository, print_job_id, lambda print_job: print_job.start_review(now)
        )

    async def approve(self, print_job_id: PrintJobId) -> PrintJob:
        now = self._clock()
        return await change_async(
            self._repository, print_job_id, lambda print_job: print_job.approve(now)
        )

    async def reject(self, print_job_id: PrintJobId, reason: str) -> PrintJob:
        now = self._clock()
        return await change_async(
            self._repository, print_job_id, lambda print_job: print_job.reject(reason, now)
        )

    async def assign(self, print_job_id: PrintJobId, printer_id: PrinterId) -> PrintJob:
        now = self._clock()
        return await change_async(
            self._repository, print_job_id, lambda print_job: print_job.assign(printer_id, now)
        )
