from collections.abc import Mapping

from connectrpc.request import RequestContext

from api.common.application_info import ApplicationInfo
from api.common.health import check_health
from api.common.models import DependencyCheck, HealthStatus
from api.gen.server.v1.health_check_connect import (
    HealthCheckRequest,
    HealthCheckResponse,
)

_RPC_STATUS = {
    HealthStatus.PASS: HealthCheckResponse.STATUS_PASS,
    HealthStatus.FAIL: HealthCheckResponse.STATUS_FAIL,
    HealthStatus.DEGRADED: HealthCheckResponse.STATUS_DEGRADED,
}


class HealthCheckServiceImplementation:
    def __init__(
        self,
        application_info: ApplicationInfo,
        dependency_functions: Mapping[str, DependencyCheck],
    ):
        self.application_info = application_info
        self.dependency_functions = dependency_functions

    async def health_check(
        self,
        request: HealthCheckRequest,
        ctx: RequestContext[HealthCheckRequest, HealthCheckResponse],
        /,
    ) -> HealthCheckResponse:
        report = await check_health(
            self.application_info,
            self.dependency_functions,
            full=request.full,
            check_dependencies=request.check_dependencies,
        )
        return HealthCheckResponse(
            status=_RPC_STATUS[report.status],
            version=report.version,
            dependencies=report.dependencies,
        )
