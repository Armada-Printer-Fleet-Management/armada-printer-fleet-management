"""The app's services over fakes, for tests that run the real app wiring with no dependencies.
The fake_app fixture in tests/conftest.py builds the app over them."""

from collections.abc import Awaitable, Callable, Mapping, Sequence
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from fastapi.testclient import TestClient

from api.app import AppServices
from api.common.authentication import Caller
from api.common.models import DependencyCheck
from api.domains.content_asset.repository import FileRepository
from api.domains.content_asset.service import FileService
from api.domains.fleet.repository import PrinterRepository
from api.domains.fleet.service import PrinterService
from api.domains.print_job.repository import PrintJobRepository
from api.domains.print_job.service import PrintJobService
from api.domains.queue.repository import PrinterQueueRepository
from api.domains.queue.service import PrinterQueueService
from api.infrastructure.dev_data import (
    stub_files,
    stub_print_jobs,
    stub_printer_queues,
    stub_printers,
)
from api.infrastructure.file_memory import InMemoryFileRepository
from api.infrastructure.file_store_files import FileStoreFiles
from api.infrastructure.print_job_memory import InMemoryPrintJobRepository
from api.infrastructure.printer_queue_memory import InMemoryPrinterQueueRepository
from api.infrastructure.printer_server_mock import MockPrinterServer
from tests.fakes import MemoryFileStore
from tests.samples import NOW


@dataclass(frozen=True)
class FakeServices:
    services: AppServices
    # Opened by the app's lifespan, on the test client's own event loop.
    resources: Sequence[AbstractAsyncContextManager[object]]


def fake_services(
    *,
    clock: Callable[[], datetime] = lambda: NOW,
    print_jobs: PrintJobRepository | None = None,
    files: FileRepository | None = None,
    store: MemoryFileStore | None = None,
    printer_server: PrinterRepository | None = None,
    printer_queues: PrinterQueueRepository | None = None,
) -> FakeServices:
    """Every service over an in-memory fake seeded from the development data, on a fixed clock.
    Pass a fake to replace the default one, such as a repository that raises Unavailable."""
    if print_jobs is None:
        print_jobs = InMemoryPrintJobRepository(stub_print_jobs())
    if files is None:
        files = InMemoryFileRepository(stub_files())
    file_store = MemoryFileStore() if store is None else store
    if printer_server is None:
        printer_server = MockPrinterServer(stub_printers(), clock)
    if printer_queues is None:
        printer_queues = InMemoryPrinterQueueRepository(stub_printer_queues())

    storage = FileStoreFiles(lambda: file_store)
    services = AppServices(
        print_jobs=PrintJobService(print_jobs, clock),
        files=FileService(files, storage, clock),
        printers=PrinterService(printer_server),
        printer_queues=PrinterQueueService(printer_queues),
    )
    return FakeServices(services, [storage])


def on_app_loop[T](client: TestClient, function: Callable[[], Awaitable[T]]) -> T:
    """Runs function on the client's own event loop, where the app's resources were opened. For a
    test that must stay sync because it uses the client."""
    assert client.portal is not None, "use the client inside its with block, as fake_app does"
    return client.portal.call(function)


class FakeApp(Protocol):
    """Builds the real app over fakes and returns a client already inside its lifespan."""

    def __call__(
        self,
        fakes: FakeServices | None = None,
        *,
        dependency_checks: Mapping[str, DependencyCheck] | None = None,
        verify: Callable[[str], Awaitable[Caller]] | None = None,
        enforce: bool = False,
    ) -> TestClient: ...
