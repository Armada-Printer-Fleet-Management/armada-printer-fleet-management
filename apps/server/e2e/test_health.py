"""As an operator, I check that the deployed server and everything it depends on are healthy."""

import httpx2
from proto_utils.gen.server.v1.health_check_connect import HealthCheckServiceClientSync
from proto_utils.gen.server.v1.health_check_pb2 import HealthCheckRequest, HealthCheckResponse


def test_the_server_and_its_dependencies_pass(rest: httpx2.Client) -> None:
    response = rest.get("/api/health_check", params={"check_dependencies": "true", "full": "true"})

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "pass", response.text


def test_the_health_rpc_agrees(health: HealthCheckServiceClientSync) -> None:
    response = health.health_check(HealthCheckRequest(full=True, check_dependencies=True))

    assert response.status == HealthCheckResponse.STATUS_PASS, dict(response.dependencies)
