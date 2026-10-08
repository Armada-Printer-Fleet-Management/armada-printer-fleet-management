"""The desktop's composition root: the only place infrastructure is constructed and handed to the
domain services that IPC exposes."""

from armada_domains.print_job.service import PrintJobService
from armada_infrastructure.application_server.connection import ApplicationServerConnection
from armada_infrastructure.application_server.print_job_repository import (
    ApplicationServerPrintJobRepository,
)
from armada_ipc import Ipc


def build_ipc() -> Ipc:
    server = ApplicationServerConnection()
    return Ipc(print_jobs=PrintJobService(ApplicationServerPrintJobRepository(server)))
