import pytest
import structlog
from fastapi.testclient import TestClient
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route
from structlog.testing import capture_logs
from structlog.typing import EventDict

from api.common.consts import API_PREFIX
from api.middleware.request_context import RequestContextMiddleware

_RPC_PATH = f"{API_PREFIX}/server.v1.HealthCheckService/HealthCheck"


def _finished(logs: list[EventDict]) -> list[EventDict]:
    return [entry for entry in logs if entry["event"] == "request finished"]


def test_logs_finished_rest_request_with_context(client: TestClient) -> None:
    with capture_logs(processors=[structlog.contextvars.merge_contextvars]) as logs:
        client.get(f"{API_PREFIX}/health_check")

    [entry] = _finished(logs)
    assert len(entry["request_id"]) == 32
    assert entry["method"] == "GET"
    assert entry["path"] == f"{API_PREFIX}/health_check"
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
        client.get(f"{API_PREFIX}/health_check")
        client.post(_RPC_PATH, json={})

    first, second = _finished(logs)
    assert first["request_id"] != second["request_id"]
    assert [first["path"], second["path"]] == [f"{API_PREFIX}/health_check", _RPC_PATH]


def test_request_id_is_not_exposed_in_the_response(client: TestClient) -> None:
    response = client.get(f"{API_PREFIX}/health_check", headers={"X-Request-ID": "abc-123"})

    assert "x-request-id" not in response.headers


async def _broken(_request: Request) -> Response:
    raise RuntimeError("route failed")


def test_a_failing_route_is_logged_as_a_500() -> None:
    app = Starlette(routes=[Route("/broken", _broken)])
    app.add_middleware(RequestContextMiddleware)

    with capture_logs(processors=[structlog.contextvars.merge_contextvars]) as logs:
        with TestClient(app) as broken_client, pytest.raises(RuntimeError, match="route failed"):
            broken_client.get("/broken")

    [entry] = _finished(logs)
    assert entry["status"] == 500
    assert entry["path"] == "/broken"
