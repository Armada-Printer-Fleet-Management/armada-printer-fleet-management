"""The token check as api/main.py wires it. The client runs no lifespan, so no dependency is open
and these tests never reach the identity provider."""

import pytest
from fastapi.testclient import TestClient

from api.common.health import overall_status
from api.common.models import HealthStatus
from api.main import app, dependency_checks


def test_the_health_check_lists_the_identity_provider() -> None:
    response = TestClient(app).get(
        "/api/health_check", params={"full": "true", "check_dependencies": "true"}
    )

    assert "identity_provider" in response.json()["dependencies"]


def test_the_identity_provider_failing_alone_only_degrades_the_service() -> None:
    statuses = {name: HealthStatus.PASS for name in dependency_checks}
    statuses["identity_provider"] = HealthStatus.FAIL

    assert overall_status(dependency_checks, statuses) == HealthStatus.DEGRADED


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/health_check"),
        ("POST", "/api/server.v1.PrintJobService/ListPrintJobs"),
    ],
    ids=["REST", "Connect"],
)
def test_a_bad_authorization_header_is_a_401_on_the_app(method: str, path: str) -> None:
    response = TestClient(app).request(
        method, path, json={}, headers={"Authorization": "Basic dXNlcjpwYXNz"}
    )

    assert response.status_code == 401
    assert response.json()["code"] == "unauthenticated"
