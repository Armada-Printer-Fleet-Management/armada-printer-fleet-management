from datetime import UTC, datetime

from connectrpc.server import ConnectASGIApplication
from fastapi import FastAPI
from organization_info import read
from proto_utils.gen.common.v1 import organization_info_pb2
from proto_utils.gen.server.v1.health_check_connect import HealthCheckServiceASGIApplication
from proto_utils.gen.server.v1.print_job_service_connect import PrintJobServiceASGIApplication
from starlette.types import Receive, Scope, Send

from api.common.consts import API_PREFIX
from api.common.dependencies import application_info, dependency_checks
from api.common.openapi import openapi_schema
from api.domains.print_job.service import PrintJobService
from api.infrastructure.print_job_sql import SqlPrintJobRepository, stub_print_jobs
from api.lifespan import lifespan
from api.middleware.request_context import RequestContextMiddleware
from api.routers.health import router as health_router
from api.services.health_check_service import HealthCheckServiceImplementation
from api.services.print_job_service import PrintJobServiceImplementation

app = FastAPI(
    title=read(organization_info_pb2.OrganizationInfo()).title,
    version=application_info().version_string(),
    lifespan=lifespan,
)
app.openapi = lambda: openapi_schema(app)
app.add_middleware(RequestContextMiddleware)
app.include_router(health_router, prefix=API_PREFIX)


# connectrpc strips the whole mount path before matching procedures, so a plain app.mount under
# API_PREFIX 404s. Trimming the service's own path off root_path leaves only the prefix to strip.
def mount_rpc[S](service: ConnectASGIApplication[S]) -> None:
    async def prefixed(scope: Scope, receive: Receive, send: Send) -> None:
        root_path = str(scope["root_path"]).removesuffix(service.path)
        await service({**scope, "root_path": root_path}, receive, send)

    app.mount(API_PREFIX + service.path, prefixed)


# The RPC service sits outside FastAPI's dependency injection, so it is handed the same cached
# instances the REST route receives through Depends.
health_check_service = HealthCheckServiceImplementation(application_info(), dependency_checks())
mount_rpc(HealthCheckServiceASGIApplication(health_check_service))

print_job_service = PrintJobService(
    SqlPrintJobRepository(stub_print_jobs()), clock=lambda: datetime.now(UTC)
)
mount_rpc(PrintJobServiceASGIApplication(PrintJobServiceImplementation(print_job_service)))
