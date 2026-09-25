import asyncio
from collections.abc import Mapping

from api.common.application_info import ApplicationInfo
from api.common.models import DependencyCheck, HealthReport, HealthStatus


async def run_dependency_checks(checks: Mapping[str, DependencyCheck]) -> dict[str, str]:
    # A check that raises counts as a failure; its message is deliberately not reported,
    # because it can carry internal details such as hostnames.
    results = await asyncio.gather(
        *(check.probe() for check in checks.values()), return_exceptions=True
    )
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
