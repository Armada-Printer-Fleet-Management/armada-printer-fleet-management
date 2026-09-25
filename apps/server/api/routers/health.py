from fastapi import APIRouter, Response, status
from fastapi.responses import PlainTextResponse

from api.common.dependencies import ApplicationInfoDep, DependencyChecksDep
from api.common.health import check_health
from api.common.models import HealthResponse, HealthStatus

router = APIRouter(
    tags=["General"],
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Service is unhealthy"},
        status.HTTP_200_OK: {"description": "Service is healthy or degraded"},
    },
)


@router.get("/health_check", response_model=HealthResponse, response_model_exclude_none=True)
async def health(
    response: Response,
    application_info: ApplicationInfoDep,
    checks: DependencyChecksDep,
    full: bool = False,
    check_dependencies: bool = False,
) -> HealthResponse | PlainTextResponse:
    report = await check_health(
        application_info, checks, full=full, check_dependencies=check_dependencies
    )
    # A degraded service still serves requests, so load balancers should keep routing to it.
    status_code = (
        status.HTTP_503_SERVICE_UNAVAILABLE
        if report.status == HealthStatus.FAIL
        else status.HTTP_200_OK
    )

    if not full:
        return PlainTextResponse(report.status, status_code=status_code)

    response.status_code = status_code
    return HealthResponse(
        status=report.status, version=report.version, dependencies=report.dependencies
    )
