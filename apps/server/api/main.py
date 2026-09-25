from fastapi import FastAPI

from api.common.consts import APP_NAME
from api.common.dependencies import application_information, dependency_checks
from api.gen.server.v1.health_check_connect import HealthCheckServiceASGIApplication
from api.routers.health import router as health_router
from api.services.health_check_service import HealthCheckServiceImplementation

app = FastAPI(title=APP_NAME)
app.include_router(health_router)

# The RPC service sits outside FastAPI's dependency injection, so it is handed the same cached
# instances the REST route receives through Depends.
health_check_service = HealthCheckServiceImplementation(
    application_information(), dependency_checks()
)
health_check_rpc = HealthCheckServiceASGIApplication(health_check_service)
app.mount(health_check_rpc.path, health_check_rpc)
