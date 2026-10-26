# Stub: plays the printer server, so the desktop can dispatch and watch prints before the server
# can reach real printers. A dispatched printer reports 25% more progress every 5 seconds and then
# FINISHED; a faulty printer reports ERROR at 50% instead. Replacing it means a printer server
# client in api/infrastructure that implements api/domains/printer/repository.py by asking the
# printer server, constructed in api/main.py.
from collections.abc import Callable, Iterable
from dataclasses import replace
from datetime import datetime, timedelta

from core_domain.ddd import EntityNotFound, InvalidPageToken, Page
from core_domain.ids import PrinterId, PrintJobId
from core_domain.printer import Printer, PrinterStatus

from api.domains.printer.repository import PrinterRepository

STEP = timedelta(seconds=5)
PERCENT_PER_STEP = 25
FAULT_AT_PERCENT = 50


class MockPrinterServer(PrinterRepository):
    def __init__(
        self,
        printers: Iterable[Printer],
        clock: Callable[[], datetime],
        faulty_printer_ids: Iterable[PrinterId] = (),
    ) -> None:
        self._clock = clock
        self._printers = {printer.id: printer for printer in printers}
        self._faulty = set(faulty_printer_ids)
        started = clock()
        self._printing_since = {
            printer.id: started
            for printer in self._printers.values()
            if printer.status is PrinterStatus.PRINTING
        }

    def _observe(self, printer_id: PrinterId) -> Printer:
        if printer_id not in self._printers:
            raise EntityNotFound(printer_id)
        printer = self._printers[printer_id]
        now = self._clock()
        if printer_id in self._printing_since:
            steps = (now - self._printing_since[printer_id]) // STEP
            progress = min(100, steps * PERCENT_PER_STEP)
            if printer_id in self._faulty and progress >= FAULT_AT_PERCENT:
                printer.progress_percent = FAULT_AT_PERCENT
                printer.status = PrinterStatus.ERROR
                del self._printing_since[printer_id]
            else:
                printer.progress_percent = progress
                if progress == 100:
                    printer.status = PrinterStatus.FINISHED
                    del self._printing_since[printer_id]
        printer.updated_at = now
        return replace(printer)

    async def get(self, entity_id: PrinterId) -> Printer:
        return self._observe(entity_id)

    async def page(self, page_size: int, page_token: str) -> Page[Printer]:
        if page_token:
            raise InvalidPageToken()
        by_name = sorted(self._printers.values(), key=lambda printer: printer.name)
        return Page([self._observe(printer.id) for printer in by_name])

    async def request_dispatch(self, printer_id: PrinterId, print_job_id: PrintJobId) -> Printer:
        printer = self._observe(printer_id)
        printer.dispatch(print_job_id, self._clock())
        self._printers[printer_id] = printer
        self._printing_since[printer_id] = printer.updated_at
        return replace(printer)

    async def request_release(self, printer_id: PrinterId) -> Printer:
        printer = self._observe(printer_id)
        printer.release(self._clock())
        self._printers[printer_id] = printer
        return replace(printer)
