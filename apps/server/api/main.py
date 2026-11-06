from datetime import timedelta

from sqlalchemy.ext.asyncio import create_async_engine

from api.app import AppParts, AppServices, build_app
from api.common.clock import clock
from api.common.health import raising_probe
from api.common.models import DependencyCheck
from api.common.settings import AuthSettings, FileStoreSettings, database_url
from api.domains.content_asset.service import FileService
from api.domains.fleet.service import PrinterService
from api.domains.print_job.service import PrintJobService
from api.domains.queue.service import PrinterQueueService
from api.infrastructure.dev_data import (
    STUB_FAULTY_PRINTER_ID,
    STUB_STUDENT_ID,
    stub_printer_queues,
    stub_printers,
)
from api.infrastructure.file_sql import SqlFileRepository
from api.infrastructure.file_store_files import FileStoreFiles
from api.infrastructure.oidc_access_tokens import OidcAccessTokens
from api.infrastructure.postgres_database import PostgresDatabase
from api.infrastructure.print_job_sql import SqlPrintJobRepository
from api.infrastructure.printer_queue_memory import InMemoryPrinterQueueRepository
from api.infrastructure.printer_server_mock import MockPrinterServer
from api.plugins import build_file_store, build_token_verifier
from api.services.printer_poller import PrinterPoller


def production_parts() -> AppParts:
    """Everything the production app runs on, built new on each call."""
    # Infrastructure
    files = FileStoreFiles(lambda: build_file_store(FileStoreSettings()))  # Built at lifespan
    database = PostgresDatabase(lambda: create_async_engine(database_url()))  # Built at lifespan
    access_tokens = OidcAccessTokens(
        lambda: build_token_verifier(AuthSettings())
    )  # Built at lifespan

    # Services (note difference from an RPC service, this is the domain service)

    # Domains without a SQL repository keep their state in memory, starting from the dev data.
    # Moving one to the database means constructing its SQL adapter here; nothing else changes.
    print_job_service = PrintJobService(SqlPrintJobRepository(database), clock)
    file_service = FileService(SqlFileRepository(database), files, clock)
    printer_service = PrinterService(
        MockPrinterServer(stub_printers(), clock, faulty_printer_ids=[STUB_FAULTY_PRINTER_ID])
    )
    printer_queue_service = PrinterQueueService(
        InMemoryPrinterQueueRepository(stub_printer_queues())
    )
    printer_poller = PrinterPoller(printer_service, print_job_service, timedelta(seconds=1))

    dependency_checks = {
        "file_storage": DependencyCheck(raising_probe(files.health_check)),
        "database": DependencyCheck(raising_probe(database.health_check)),
        # Requests without a token still work while the identity provider is down.
        "identity_provider": DependencyCheck(
            raising_probe(access_tokens.health_check), critical=False
        ),
    }

    return AppParts(
        services=AppServices(
            print_jobs=print_job_service,
            files=file_service,
            printers=printer_service,
            printer_queues=printer_queue_service,
        ),
        # Stub: every caller is the seeded student until the server authenticates requests.
        caller=lambda: STUB_STUDENT_ID,
        verify=access_tokens.verify,
        enforce=AuthSettings().enforce,
        dependency_checks=dependency_checks,
        resources=[files, database, access_tokens],
        background=[printer_poller.run],
    )


app = build_app(production_parts())
