import asyncio
from collections.abc import Mapping

import structlog

from api.common.application_info import ApplicationInfo
from api.common.models import DependencyCheck, HealthReport, HealthStatus

logger = structlog.stdlib.get_logger(__name__)

# A dependency that hangs must not hang the health endpoint with it.
DEPENDENCY_CHECK_TIMEOUT_SECONDS = 3.0


async def run_dependency_checks(checks: Mapping[str, DependencyCheck]) -> dict[str, str]:
    # A check that raises or times out counts as a failure; its message is logged but
    # deliberately not reported, because it can carry internal details such as hostnames.
    results = await asyncio.gather(
        *(
            asyncio.wait_for(check.probe(), DEPENDENCY_CHECK_TIMEOUT_SECONDS)
            for check in checks.values()
        ),
        return_exceptions=True,
    )
    for name, result in zip(checks.keys(), results, strict=True):
        if isinstance(result, BaseException):
            logger.warning("dependency check failed", dependency=name, exc_info=result)
    return {
        name: HealthStatus.PASS if result is True else HealthStatus.FAIL
        for name, result in zip(checks.keys(), results, strict=True)
    }


def overall_status(
    checks: Mapping[str, DependencyCheck], dependencies: Mapping[str, str]
) -> HealthStatus:
    failed = [checks[name] for name, status in dependencies.items() if status != HealthStatus.PASS]
    if any(check.critical for check in failed):
        return HealthStatus.FAIL
    if failed:
        return HealthStatus.DEGRADED
    return HealthStatus.PASS


async def check_health(
    application_info: ApplicationInfo,
    checks: Mapping[str, DependencyCheck],
    *,
    full: bool,
    check_dependencies: bool,
) -> HealthReport:
    dependencies = await run_dependency_checks(checks) if check_dependencies else {}
    return HealthReport(
        status=overall_status(checks, dependencies),
        version=application_info.version_string() if full else None,
        dependencies=dependencies if full and check_dependencies else None,
    )
