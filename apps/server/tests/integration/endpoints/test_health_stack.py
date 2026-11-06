from fastapi.testclient import TestClient

_RPC_PATH = "/api/server.v1.HealthCheckService/HealthCheck"
_ALL_REAL_DEPENDENCIES_PASS = {
    "database": "pass",
    "file_storage": "pass",
    "identity_provider": "pass",
}


def test_health_passes_against_every_real_dependency(app_client: TestClient) -> None:
    response = app_client.get(
        "/api/health_check", params={"full": True, "check_dependencies": True}
    )

    assert response.status_code == 200
    assert response.json()["status"] == "pass"
    assert response.json()["dependencies"] == _ALL_REAL_DEPENDENCIES_PASS


def test_rpc_is_mounted_on_the_app(app_client: TestClient) -> None:
    response = app_client.post(_RPC_PATH, json={})

    assert response.status_code == 200
    assert response.json() == {"status": "STATUS_PASS"}


def test_rpc_passes_against_every_real_dependency(app_client: TestClient) -> None:
    response = app_client.post(_RPC_PATH, json={"full": True, "checkDependencies": True})

    assert response.status_code == 200
    assert response.json()["status"] == "STATUS_PASS"
    assert response.json()["dependencies"] == _ALL_REAL_DEPENDENCIES_PASS
