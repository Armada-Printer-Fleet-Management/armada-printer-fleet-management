"""The app's services over fakes, for tests that run the real app wiring with no dependencies.
The fake_app fixture in tests/conftest.py builds the app over them."""

from collections.abc import Awaitable, Callable, Mapping, Sequence
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from fastapi.testclient import TestClient
from organization_info import read
from proto_utils.gen.organization.v1 import organization_info_pb2
from proto_utils.mappers import AgreementMapper

from api.app import AppServices
from api.common.authentication import Caller
from api.common.models import DependencyCheck
from api.domains.auth.repository import UserRepository
from api.domains.auth.service import UserService
from api.domains.content_asset.repository import FileRepository
from api.domains.content_asset.service import FileService
from api.domains.fleet.repository import PrinterRepository
from api.domains.fleet.service import PrinterService
from api.domains.legal.repository import AgreementRepository
from api.domains.legal.service import AgreementService
from api.domains.print_job.repository import PrintJobRepository
from api.domains.print_job.service import PrintJobService
from api.domains.print_preparation.service import SlicerConfigurationService
from api.domains.queue.repository import PrinterQueueRepository
from api.domains.queue.service import PrinterQueueService
from api.infrastructure.agreement_memory import InMemoryAgreementRepository
from api.infrastructure.dev_data import (
    stub_files,
    stub_print_jobs,
    stub_printer_queues,
    stub_printers,
    stub_users,
)
from api.infrastructure.file_memory import InMemoryFileRepository
from api.infrastructure.file_store_files import FileStoreFiles
from api.infrastructure.print_job_memory import InMemoryPrintJobRepository
from api.infrastructure.printer_queue_memory import InMemoryPrinterQueueRepository
from api.infrastructure.printer_server_mock import MockPrinterServer
from api.infrastructure.slice_profile_stub import StubSliceProfiles
from api.infrastructure.user_memory import InMemoryUserRepository
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
    agreements: AgreementRepository | None = None,
    users: UserRepository | None = None,
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
    if agreements is None:
        agreements = InMemoryAgreementRepository()
    documents = [
        AgreementMapper.legal_document_from_proto(document)
        for document in read(organization_info_pb2.OrganizationInfo()).legal_documents
    ]
    if users is None:
        users = InMemoryUserRepository(stub_users())

    storage = FileStoreFiles(lambda: file_store)
    services = AppServices(
        print_jobs=PrintJobService(print_jobs, clock),
        files=FileService(files, storage, clock),
        printers=PrinterService(printer_server),
        printer_queues=PrinterQueueService(printer_queues),
        agreements=AgreementService(agreements, documents, clock),
        slicer_configuration=SlicerConfigurationService(StubSliceProfiles()),
        users=UserService(users, clock),
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
