from collections.abc import Mapping
from dataclasses import dataclass

from api.common.application_information import ApplicationInformation
from api.common.dependency_checks import DependencyCheck, all_passed, run_dependency_checks


@dataclass(frozen=True)
class HealthReport:
    healthy: bool
    version: str | None
    dependencies: dict[str, str] | None


async def check_health(
    application_information: ApplicationInformation,
    checks: Mapping[str, DependencyCheck],
    *,
    full: bool,
    check_dependencies: bool,
) -> HealthReport:
    dependencies = await run_dependency_checks(checks) if check_dependencies else {}
    return HealthReport(
        healthy=all_passed(dependencies),
        version=application_information.version_string() if full else None,
        dependencies=dependencies if full and check_dependencies else None,
    )
