import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from core_domain.ddd import Page
from core_domain.fleet import Printer, PrinterStatus
from core_domain.ids import PrinterId, PrintJobId
from core_domain.print_job import PrintJob, PrintJobStatus

from api.domains.fleet.service import PrinterService
from api.domains.print_job.service import PrintJobService
from api.infrastructure.dev_data import (
    STUB_APPROVED_JOB_ID,
    STUB_FAULTY_PRINTER_ID,
    STUB_IDLE_PRINTER_ID,
    STUB_PRINTER_QUEUE_ID,
    STUB_STUDENT_ID,
    stub_print_jobs,
    stub_printers,
)
from api.infrastructure.print_job_memory import InMemoryPrintJobRepository
from api.infrastructure.printer_server_mock import STEP, MockPrinterServer
from api.services.printer_poller import PrinterPoller


class Clock:
    def __init__(self) -> None:
        self.now = datetime(2026, 10, 7, 12, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now


def dispatch_approved_job() -> tuple[Clock, PrinterService, PrintJobService, PrinterPoller]:
    clock = Clock()
    printers = PrinterService(MockPrinterServer(stub_printers(), clock))
    print_jobs = PrintJobService(InMemoryPrintJobRepository(stub_print_jobs()), clock)
    poller = PrinterPoller(printers, print_jobs, timedelta(seconds=1))

    async def dispatch() -> bool:
        printer = await printers.dispatch(STUB_IDLE_PRINTER_ID, STUB_APPROVED_JOB_ID)
        return printer.print_job_id == STUB_APPROVED_JOB_ID

    asyncio.run(print_jobs.assign(STUB_APPROVED_JOB_ID, STUB_IDLE_PRINTER_ID, dispatch))
    return clock, printers, print_jobs, poller


def test_poll_moves_a_job_to_printing_once_its_printer_reports_it() -> None:
    _, _, print_jobs, poller = dispatch_approved_job()

    asyncio.run(poller.poll())

    assert asyncio.run(print_jobs.print_job(STUB_APPROVED_JOB_ID)).status is (
        PrintJobStatus.PRINTING
    )


def test_a_printer_that_finishes_moves_its_job_to_finished_never_completed() -> None:
    clock, printers, print_jobs, poller = dispatch_approved_job()
    asyncio.run(poller.poll())

    clock.now += STEP * 4
    asyncio.run(poller.poll())

    printer = asyncio.run(printers.get(STUB_IDLE_PRINTER_ID))
    assert (printer.status, printer.progress_percent) == (PrinterStatus.FINISHED, 100)
    # Only staff complete a job, after checking the print.
    assert asyncio.run(print_jobs.print_job(STUB_APPROVED_JOB_ID)).status is (
        PrintJobStatus.FINISHED
    )


def test_run_keeps_polling_after_an_unexpected_error(monkeypatch: pytest.MonkeyPatch) -> None:
    _, printers, print_jobs, _ = dispatch_approved_job()
    poller = PrinterPoller(printers, print_jobs, timedelta(0))
    polls: list[None] = []

    async def poll() -> None:
        polls.append(None)
        if len(polls) == 1:
            raise RuntimeError("the printer server sent something unreadable")
        raise asyncio.CancelledError

    monkeypatch.setattr(poller, "poll", poll)
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(poller.run())
    assert len(polls) == 2


def test_a_printer_fault_leaves_the_job_for_staff_and_ready_clears_it() -> None:
    clock = Clock()
    printers = PrinterService(
        MockPrinterServer(stub_printers(), clock, faulty_printer_ids=[STUB_IDLE_PRINTER_ID])
    )
    print_jobs = PrintJobService(InMemoryPrintJobRepository(stub_print_jobs()), clock)
    poller = PrinterPoller(printers, print_jobs, timedelta(seconds=1))

    async def dispatch() -> bool:
        printer = await printers.dispatch(STUB_IDLE_PRINTER_ID, STUB_APPROVED_JOB_ID)
        return printer.print_job_id == STUB_APPROVED_JOB_ID

    asyncio.run(print_jobs.assign(STUB_APPROVED_JOB_ID, STUB_IDLE_PRINTER_ID, dispatch))
    asyncio.run(poller.poll())
    clock.now += STEP * 4
    asyncio.run(poller.poll())

    faulted = asyncio.run(printers.get(STUB_IDLE_PRINTER_ID))
    assert (faulted.status, faulted.progress_percent) == (PrinterStatus.ERROR, 50)
    assert asyncio.run(print_jobs.print_job(STUB_APPROVED_JOB_ID)).status is (
        PrintJobStatus.PRINTING
    )
    assert asyncio.run(printers.release(STUB_IDLE_PRINTER_ID)).status is PrinterStatus.IDLE


class TwoPagePrinterServer(MockPrinterServer):
    """Serves the seeded printers as two pages, the first three by name and then the rest."""

    async def page(self, page_size: int, page_token: str) -> Page[Printer]:
        by_name = (await super().page(0, "")).items
        return Page(by_name[3:]) if page_token else Page(by_name[:3], "next")


def test_poll_reads_every_page_of_printers() -> None:
    clock = Clock()
    printers = PrinterService(TwoPagePrinterServer(stub_printers(), clock))
    repository = InMemoryPrintJobRepository(stub_print_jobs())
    second_job = PrintJob(
        PrintJobId.new(),
        STUB_STUDENT_ID,
        PrintJobStatus.APPROVED,
        clock.now,
        clock.now,
        "notes",
        printer_queue_id=STUB_PRINTER_QUEUE_ID,
    )
    asyncio.run(repository.save(second_job))
    print_jobs = PrintJobService(repository, clock)
    # Stub printer 1 is on the first page and stub printer 6 on the second.
    for job_id, printer_id in (
        (STUB_APPROVED_JOB_ID, STUB_IDLE_PRINTER_ID),
        (second_job.id, STUB_FAULTY_PRINTER_ID),
    ):

        async def dispatch(job_id: PrintJobId = job_id, printer_id: PrinterId = printer_id) -> bool:
            return (await printers.dispatch(printer_id, job_id)).print_job_id == job_id

        asyncio.run(print_jobs.assign(job_id, printer_id, dispatch))

    asyncio.run(PrinterPoller(printers, print_jobs, timedelta(seconds=1)).poll())

    for job_id in (STUB_APPROVED_JOB_ID, second_job.id):
        assert asyncio.run(print_jobs.print_job(job_id)).status is PrintJobStatus.PRINTING
