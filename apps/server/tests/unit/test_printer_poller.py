import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from core_domain.print_job import PrintJobStatus
from core_domain.printer import PrinterStatus

from api.domains.print_job.service import PrintJobService
from api.domains.printer.service import PrinterService
from api.infrastructure.dev_data import (
    STUB_APPROVED_JOB_ID,
    STUB_IDLE_PRINTER_ID,
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
