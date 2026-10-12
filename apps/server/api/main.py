from datetime import UTC, datetime

from connectrpc.server import ConnectASGIApplication
from fastapi import FastAPI
from organization_info import read
from proto_utils.gen.common.v1 import organization_info_pb2
from proto_utils.gen.server.v1.health_check_connect import HealthCheckServiceASGIApplication
from proto_utils.gen.server.v1.print_job_service_connect import PrintJobServiceASGIApplication
from starlette.types import Receive, Scope, Send

from api.common.consts import API_PREFIX
from api.common.dependencies import application_info
from api.common.models import DependencyCheck
from api.common.openapi import openapi_schema
from api.common.settings import FileStoreSettings
from api.domains.file.service import FileService
from api.domains.print_job.service import PrintJobService
from api.infrastructure.file_memory import InMemoryFileRepository
from api.infrastructure.file_storage_mock import MockFileStorage
from api.infrastructure.file_store_files import FileStoreFiles
from api.infrastructure.print_job_memory import InMemoryPrintJobRepository
from api.infrastructure.stub_data import STUB_STUDENT_ID, stub_files, stub_print_jobs
from api.lifespan import lifespan
from api.middleware.request_context import RequestContextMiddleware
from api.plugins import build_file_store
from api.routers.health import health_router
from api.services.health_check_service import HealthCheckServiceImplementation
from api.services.print_job_service import PrintJobServiceImplementation

# Infrastructure owns the plugin: the adapter builds the store when the lifespan opens it, so
# importing this module reads no file store configuration.
files = FileStoreFiles(lambda: build_file_store(FileStoreSettings()))


async def file_storage_reachable() -> bool:
    await files.health_check()
    return True


# The REST route and the RPC service both report these same checks.
dependency_checks = {"file_storage": DependencyCheck(file_storage_reachable)}

app = FastAPI(
    title=read(organization_info_pb2.OrganizationInfo()).title,
    version=application_info().version_string(),
    lifespan=lifespan(files),
)
app.openapi = lambda: openapi_schema(app)
app.add_middleware(RequestContextMiddleware)
app.include_router(health_router(dependency_checks), prefix=API_PREFIX)


# connectrpc strips the whole mount path before matching procedures, so a plain app.mount under
# API_PREFIX 404s. Trimming the service's own path off root_path leaves only the prefix to strip.
def mount_rpc[S](service: ConnectASGIApplication[S]) -> None:
    async def prefixed(scope: Scope, receive: Receive, send: Send) -> None:
        root_path = str(scope["root_path"]).removesuffix(service.path)
        await service({**scope, "root_path": root_path}, receive, send)

    app.mount(API_PREFIX + service.path, prefixed)


# The RPC service sits outside FastAPI's dependency injection, so it is handed the same cached
# instances the REST route receives.
health_check_service = HealthCheckServiceImplementation(application_info(), dependency_checks)
mount_rpc(HealthCheckServiceASGIApplication(health_check_service))


def clock() -> datetime:
    return datetime.now(UTC)


# The in-memory repositories and mock storage stand in until the server has a database and an
# object store. Switching means constructing the real adapters here; nothing else changes.
print_job_service = PrintJobService(InMemoryPrintJobRepository(stub_print_jobs()), clock)
file_service = FileService(InMemoryFileRepository(stub_files()), MockFileStorage(), clock)
# Stub: every caller is the seeded student until the server authenticates requests.
print_job_handler = PrintJobServiceImplementation(
    print_job_service, file_service, caller=lambda: STUB_STUDENT_ID
)
mount_rpc(PrintJobServiceASGIApplication(print_job_handler))
