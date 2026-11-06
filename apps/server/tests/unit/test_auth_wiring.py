"""The token check as api/main.py wires it, without running the app."""

from api.common.health import overall_status
from api.common.models import HealthStatus
from api.main import production_parts


def test_the_identity_provider_failing_alone_only_degrades_the_service() -> None:
    dependency_checks = production_parts().dependency_checks
    statuses = {name: HealthStatus.PASS for name in dependency_checks}
    statuses["identity_provider"] = HealthStatus.FAIL

    assert overall_status(dependency_checks, statuses) == HealthStatus.DEGRADED
