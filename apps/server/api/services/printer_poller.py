import asyncio
from datetime import timedelta

import structlog
from core_domain.printer import PrinterStatus

from api.domains.print_job.service import PrintJobService
from api.domains.printer.service import PrinterService

logger = structlog.stdlib.get_logger(__name__)


class PrinterPoller:
    """Reads every printer on an interval and applies what the printers report to their print
    jobs: PRINTING when the print starts and FINISHED when it ends. Only staff complete a job."""

    def __init__(
        self, printers: PrinterService, print_jobs: PrintJobService, interval: timedelta
    ) -> None:
        self._printers = printers
        self._print_jobs = print_jobs
        self._interval = interval

    async def poll(self) -> None:
        page_token = ""
        while True:
            page = await self._printers.page(0, page_token)
            for printer in page.items:
                if printer.print_job_id is None:
                    continue
                print_job = await self._print_jobs.print_job(printer.print_job_id)
                printing = printer.status in (PrinterStatus.PRINTING, PrinterStatus.FINISHED)
                if print_job.can_start_printing(printer_printing=printing):
                    print_job = await self._print_jobs.start_printing(print_job.id, printing)
                finished = printer.status is PrinterStatus.FINISHED
                if print_job.can_finish(printer_finished=finished):
                    await self._print_jobs.finish(print_job.id, finished)
            if not page.next_page_token:
                return
            page_token = page.next_page_token

    async def run(self) -> None:
        """Polls until cancelled. A failed poll is logged and retried on the next interval."""
        while True:
            try:
                await self.poll()
            # Any failure is caught, or one bad poll would end the task silently. Cancellation
            # is not an Exception, so shutdown still stops the loop.
            except Exception:
                logger.exception("printer poll failed")
            await asyncio.sleep(self._interval.total_seconds())
