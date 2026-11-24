from datetime import timedelta

from organization_info import read
from proto_utils.gen.organization.v1 import organization_info_pb2
from proto_utils.mappers import AgreementMapper
from sqlalchemy.ext.asyncio import create_async_engine

from api.app import AppParts, AppServices, build_app
from api.common.clock import clock
from api.common.health import raising_probe
from api.common.models import DependencyCheck
from api.common.settings import DevDataSettings, database_url
from api.domains.auth.service import UserService
from api.domains.content_asset.service import FileService
from api.domains.fleet.service import PrinterService
from api.domains.legal.service import AgreementService
from api.domains.print_job.service import PrintJobService
from api.domains.print_preparation.service import SlicerConfigurationService
from api.domains.queue.service import PrinterQueueService
from api.infrastructure.agreement_sql import SqlAgreementRepository
from api.infrastructure.auth.identity_directory_accounts import IdentityDirectoryAccounts
from api.infrastructure.auth.identity_directory_settings import IdentitySettings
from api.infrastructure.auth.oidc_access_tokens import OidcAccessTokens
from api.infrastructure.auth.token_verifier_settings import AuthSettings
from api.infrastructure.content_asset.file_store_files import FileStoreFiles
from api.infrastructure.content_asset.file_store_settings import FileStoreSettings
from api.infrastructure.dev_data import (
    STUB_FAULTY_PRINTER_ID,
    STUB_STUDENT_ID,
    stub_idle_printers,
    stub_printer_queues,
    stub_printers,
)
from api.infrastructure.file_sql import SqlFileRepository
from api.infrastructure.postgres_database import PostgresDatabase
from api.infrastructure.print_job_sql import SqlPrintJobRepository
from api.infrastructure.printer_queue_memory import InMemoryPrinterQueueRepository
from api.infrastructure.printer_server_mock import MockPrinterServer
from api.infrastructure.slice_profile_stub import StubSliceProfiles
from api.infrastructure.user_sql import SqlUserRepository
from api.plugins import build_file_store, build_identity_directory, build_token_verifier
from api.services.printer_poller import PrinterPoller


def production_parts() -> AppParts:
    """Everything the production app runs on, built new on each call."""
    # Infrastructure
    files = FileStoreFiles(lambda: build_file_store(FileStoreSettings()))  # Built at lifespan
    database = PostgresDatabase(lambda: create_async_engine(database_url()))  # Built at lifespan
    access_tokens = OidcAccessTokens(
        lambda: build_token_verifier(AuthSettings())
    )  # Built at lifespan
    accounts = IdentityDirectoryAccounts(
        lambda: build_identity_directory(IdentitySettings())
    )  # Built at lifespan

    # Services (note difference from an RPC service, this is the domain service)

    print_job_service = PrintJobService(SqlPrintJobRepository(database), clock)
    file_service = FileService(SqlFileRepository(database), files, clock)

    # In memory services need to seeded directly unlike the SQL databases.
    dev_data = DevDataSettings().dev_data
    printer_service = PrinterService(
        MockPrinterServer(
            stub_printers() if dev_data else stub_idle_printers(),
            clock,
            faulty_printer_ids=[STUB_FAULTY_PRINTER_ID],
        )
    )
    printer_queue_service = PrinterQueueService(
        InMemoryPrinterQueueRepository(stub_printer_queues())
    )

    user_service = UserService(SqlUserRepository(database), accounts, clock)
    printer_poller = PrinterPoller(printer_service, print_job_service, timedelta(seconds=1))
    agreement_service = AgreementService(
        SqlAgreementRepository(database),
        [
            AgreementMapper.legal_document_from_proto(document)
            for document in read(organization_info_pb2.OrganizationInfo()).legal_documents
        ],
        clock,
    )
    slicer_configuration_service = SlicerConfigurationService(StubSliceProfiles())

    dependency_checks = {
        "file_storage": DependencyCheck(raising_probe(files.health_check)),
        "database": DependencyCheck(raising_probe(database.health_check)),
        # Requests without a token still work while the identity provider is down.
        "identity_provider": DependencyCheck(
            raising_probe(access_tokens.health_check), critical=False
        ),
        # The provider's account management, signed in with the server's own client. Only
        # creating users needs it, so everything else works while it is down.
        "identity_provider_accounts": DependencyCheck(
            raising_probe(accounts.health_check), critical=False
        ),
    }

    return AppParts(
        services=AppServices(
            print_jobs=print_job_service,
            files=file_service,
            printers=printer_service,
            printer_queues=printer_queue_service,
            agreements=agreement_service,
            slicer_configuration=slicer_configuration_service,
            users=user_service,
        ),
        # Stub: every caller is the seeded student until the server authenticates requests.
        caller=lambda: STUB_STUDENT_ID,
        verify=access_tokens.verify,
        enforce=AuthSettings().enforce,
        dependency_checks=dependency_checks,
        resources=[files, database, access_tokens, accounts],
        background=[printer_poller.run],
    )


app = build_app(production_parts())
