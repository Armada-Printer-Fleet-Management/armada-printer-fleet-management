from datetime import UTC, datetime

import pytest
from core_domain.ddd import Page
from core_domain.fleet import Printer

from api.domains.fleet.service import PAGE_SIZES, PrinterService
from api.infrastructure.dev_data import stub_printers
from api.infrastructure.printer_server_mock import MockPrinterServer


class SizeRecordingPrinterServer(MockPrinterServer):
    """The mock printer server, which returns every printer whatever size is asked for, noting
    the size each page was asked for."""

    def __init__(self) -> None:
        super().__init__(stub_printers(), lambda: datetime.now(UTC))
        self.requested_sizes: list[int] = []

    async def page(self, page_size: int, page_token: str) -> Page[Printer]:
        self.requested_sizes.append(page_size)
        return await super().page(page_size, page_token)


@pytest.mark.parametrize(
    ("requested", "applied"),
    [(0, PAGE_SIZES.default), (2, 2), (PAGE_SIZES.maximum + 1, PAGE_SIZES.maximum)],
)
async def test_page_applies_the_default_and_the_cap(requested: int, applied: int) -> None:
    printer_server = SizeRecordingPrinterServer()

    await PrinterService(printer_server).page(requested, "")

    assert printer_server.requested_sizes == [applied]
