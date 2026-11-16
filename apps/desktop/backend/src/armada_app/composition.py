"""The desktop's composition root: the only place infrastructure is constructed and handed to the
domain services that IPC exposes."""

from datetime import UTC, datetime

from organization_info import read
from proto_utils.gen.organization.v1 import organization_info_pb2
from proto_utils.mappers import AgreementMapper

from armada_domains.auth.service import SessionService
from armada_domains.content_asset.service import FileService
from armada_domains.fleet.service import PrinterService
from armada_domains.legal.service import AgreementService
from armada_domains.print_job.service import PrintJobService
from armada_domains.print_preparation.service import SlicerConfigurationService
from armada_domains.queue.service import PrinterQueueService
from armada_infrastructure.application_server.connection import ApplicationServerConnection
from armada_infrastructure.application_server.file import ApplicationServerFiles
from armada_infrastructure.application_server.print_job import ApplicationServerPrintJobs
from armada_infrastructure.application_server.printer import ApplicationServerPrinters
from armada_infrastructure.application_server.printer_queue import ApplicationServerPrinterQueues
from armada_infrastructure.application_server.slicer_configuration import (
    ApplicationServerSlicerConfiguration,
)
from armada_infrastructure.identity_provider.oidc_sessions import OidcSessions
from armada_infrastructure.local_agreements import LocalAgreements
from armada_infrastructure.temp_user import temp_user_id
from armada_ipc import Ipc
from armada_runtime.environment import Environment
from armada_runtime.settings import DEV_AUTH_ISSUER, DEV_SERVER_URL, load_settings


def build_ipc() -> Ipc:
    settings_path = Environment.settings_path()
    settings = load_settings(
        settings_path,
        default_server_url=DEV_SERVER_URL if Environment.is_dev else "",
        default_auth_issuer=DEV_AUTH_ISSUER if Environment.is_dev else "",
    )
    sessions = OidcSessions(settings.auth_issuer, settings.auth_client_id, settings_path)
    server = ApplicationServerConnection(
        settings.server_url, settings_path, access_token=sessions.access_token
    )
    legal_documents = read(organization_info_pb2.OrganizationInfo()).legal_documents
    return Ipc(
        print_jobs=PrintJobService(ApplicationServerPrintJobs(server)),
        printers=PrinterService(ApplicationServerPrinters(server)),
        printer_queues=PrinterQueueService(ApplicationServerPrinterQueues(server)),
        files=FileService(ApplicationServerFiles(server)),
        # TEMP: kept on this computer until the desktop signs in; see local_agreements.py.
        agreements=AgreementService(
            LocalAgreements(
                Environment.local_agreements_path(),
                [AgreementMapper.legal_document_from_proto(d) for d in legal_documents],
                lambda: datetime.now(UTC),
            ),
            temp_user_id(Environment.temp_user_id_path()),
        ),
        legal_documents=legal_documents,
        slicer_configuration=SlicerConfigurationService(
            ApplicationServerSlicerConfiguration(server)
        ),
        sessions=SessionService(sessions),
    )
