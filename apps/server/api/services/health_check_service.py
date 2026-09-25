from collections.abc import Mapping

from connectrpc.request import RequestContext

from api.common.application_information import ApplicationInformation
from api.common.dependency_checks import DependencyCheck
from api.common.health import check_health
from api.gen.server.v1.health_check_connect import (
    HealthCheckRequest,
    HealthCheckResponse,
)


class HealthCheckServiceImplementation:
    def __init__(
        self,
        application_information: ApplicationInformation,
        dependency_functions: Mapping[str, DependencyCheck],
    ):
        self.application_information = application_information
        self.dependency_functions = dependency_functions

    async def health_check(
        self,
        request: HealthCheckRequest,
        ctx: RequestContext[HealthCheckRequest, HealthCheckResponse],
        /,
    ) -> HealthCheckResponse:
        report = await check_health(
            self.application_information,
            self.dependency_functions,
            full=request.full,
            check_dependencies=request.check_dependencies,
        )
        return HealthCheckResponse(
            status=HealthCheckResponse.STATUS_PASS
            if report.healthy
            else HealthCheckResponse.STATUS_FAIL,
            version=report.version,
            dependencies=report.dependencies,
        )
