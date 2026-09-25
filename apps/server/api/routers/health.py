from fastapi import APIRouter, Response, status
from fastapi.responses import JSONResponse, PlainTextResponse

from api.common.dependencies import ApplicationInformationDep, DependencyChecksDep
from api.common.health import check_health
from api.common.models import HealthResponse

router = APIRouter()


@router.get("/health_check", response_model=None)
async def health(
    application_information: ApplicationInformationDep,
    checks: DependencyChecksDep,
    full: bool = False,
    check_dependencies: bool = False,
) -> Response:
    report = await check_health(
        application_information, checks, full=full, check_dependencies=check_dependencies
    )
    status_word = "pass" if report.healthy else "fail"
    status_code = status.HTTP_200_OK if report.healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    if not full:
        return PlainTextResponse(status_word, status_code=status_code)

    body = HealthResponse(
        status=status_word, version=report.version, dependencies=report.dependencies
    )
    return JSONResponse(body.model_dump(exclude_none=True), status_code=status_code)
