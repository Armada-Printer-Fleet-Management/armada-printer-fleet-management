from fastapi import FastAPI
from organization_info import read

from api.common.dependencies import application_info, dependency_checks
from api.common.openapi import openapi_schema
from api.gen.common.v1 import organization_info_pb2
from api.gen.server.v1.health_check_connect import HealthCheckServiceASGIApplication
from api.lifespan import lifespan
from api.middleware.request_context import RequestContextMiddleware
from api.routers.health import router as health_router
from api.services.health_check_service import HealthCheckServiceImplementation

app = FastAPI(
    title=read(organization_info_pb2.OrganizationInfo()).title,
    version=application_info().version_string(),
    lifespan=lifespan,
)
app.openapi = lambda: openapi_schema(app)
app.add_middleware(RequestContextMiddleware)
app.include_router(health_router)

# The RPC service sits outside FastAPI's dependency injection, so it is handed the same cached
# instances the REST route receives through Depends.
health_check_service = HealthCheckServiceImplementation(application_info(), dependency_checks())
health_check_rpc = HealthCheckServiceASGIApplication(health_check_service)
app.mount(health_check_rpc.path, health_check_rpc)
