from collections.abc import MutableMapping
from typing import Any

import pytest
import structlog
from fastapi.testclient import TestClient
from structlog.testing import capture_logs

from api.main import app

_RPC_PATH = "/api/server.v1.HealthCheckService/HealthCheck"


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _finished(logs: list[MutableMapping[str, Any]]) -> list[MutableMapping[str, Any]]:
    return [entry for entry in logs if entry["event"] == "request finished"]


def test_logs_finished_rest_request_with_context(client: TestClient) -> None:
    with capture_logs(processors=[structlog.contextvars.merge_contextvars]) as logs:
        client.get("/api/health_check")

    [entry] = _finished(logs)
    assert len(entry["request_id"]) == 32
    assert entry["method"] == "GET"
    assert entry["path"] == "/api/health_check"
    assert entry["status"] == 200
    assert entry["duration_ms"] >= 0


def test_logs_finished_rpc_request_with_procedure_path(client: TestClient) -> None:
    with capture_logs(processors=[structlog.contextvars.merge_contextvars]) as logs:
        client.post(_RPC_PATH, json={})

    [entry] = _finished(logs)
    assert entry["method"] == "POST"
    assert entry["path"] == _RPC_PATH
    assert entry["status"] == 200


def test_requests_do_not_share_context(client: TestClient) -> None:
    with capture_logs(processors=[structlog.contextvars.merge_contextvars]) as logs:
        client.get("/api/health_check")
        client.post(_RPC_PATH, json={})

    first, second = _finished(logs)
    assert first["request_id"] != second["request_id"]
    assert [first["path"], second["path"]] == ["/api/health_check", _RPC_PATH]


def test_request_id_is_not_exposed_in_the_response(client: TestClient) -> None:
    response = client.get("/api/health_check", headers={"X-Request-ID": "abc-123"})

    assert "x-request-id" not in response.headers
