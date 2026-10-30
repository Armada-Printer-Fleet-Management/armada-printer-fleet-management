"""AuthenticationMiddleware around a one-route app, with a fake verify and a small access table."""

import pytest
from fastapi.testclient import TestClient
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from structlog.testing import capture_logs

from api.common.access_policy import PUBLIC, STAFF, AccessPolicy, Endpoint
from api.common.authentication import Caller, InvalidAccessToken, Role, current_caller
from api.middleware.authentication import AuthenticationMiddleware

CALLERS = {
    "student-token": Caller("student", frozenset({Role.STUDENT})),
    "staff-token": Caller("staff", frozenset({Role.STAFF})),
}

POLICY = AccessPolicy({Endpoint("GET", "/public"): PUBLIC, Endpoint("GET", "/staff"): STAFF})


async def verify(token: str) -> Caller:
    if token not in CALLERS:
        raise InvalidAccessToken
    return CALLERS[token]


async def who(_request: Request) -> JSONResponse:
    caller = current_caller()
    return JSONResponse({"caller": caller.subject if caller else None})


def client(enforce: bool = False) -> TestClient:
    app = Starlette(routes=[Route("/public", who), Route("/staff", who)])
    app.add_middleware(AuthenticationMiddleware, verify=verify, policy=POLICY, enforce=enforce)
    return TestClient(app)


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# 401 for bad tokens


@pytest.mark.parametrize(
    "authorization",
    ["Bearer not-a-known-token", "Basic dXNlcjpwYXNz", "Bearer "],
    ids=["rejected token", "not bearer", "empty bearer"],
)
def test_a_bad_authorization_header_is_a_401(authorization: str) -> None:
    response = client().get("/public", headers={"Authorization": authorization})

    assert response.status_code == 401
    assert response.json() == {"code": "unauthenticated", "message": "access token is invalid"}
    assert response.headers["www-authenticate"] == 'Bearer error="invalid_token"'


# No token passes through


def test_a_request_without_a_token_runs_with_no_caller() -> None:
    response = client().get("/public")

    assert response.status_code == 200
    assert response.json() == {"caller": None}


def test_a_valid_token_makes_its_caller_current() -> None:
    response = client().get("/public", headers=bearer("student-token"))

    assert response.json() == {"caller": "student"}


# Enforce off vs on


def _denials(logs: list[dict[str, object]]) -> list[object]:
    return [entry["decision"] for entry in logs if "denied" in str(entry["event"])]


@pytest.mark.parametrize(
    "headers",
    [{}, bearer("student-token")],
    ids=["no token", "role not allowed"],
)
def test_a_refusal_is_logged_and_passes_when_not_enforced(headers: dict[str, str]) -> None:
    with capture_logs() as logs:
        response = client(enforce=False).get("/staff", headers=headers)

    assert response.status_code == 200
    assert len(_denials(logs)) == 1


@pytest.mark.parametrize(
    ("headers", "status", "code"),
    [({}, 401, "unauthenticated"), (bearer("student-token"), 403, "permission_denied")],
    ids=["no token", "role not allowed"],
)
def test_a_refusal_is_rejected_when_enforced(
    headers: dict[str, str], status: int, code: str
) -> None:
    with capture_logs() as logs:
        response = client(enforce=True).get("/staff", headers=headers)

    assert response.status_code == status
    assert response.json()["code"] == code
    assert len(_denials(logs)) == 1


def test_an_allowed_caller_is_not_logged_when_enforced() -> None:
    with capture_logs() as logs:
        response = client(enforce=True).get("/staff", headers=bearer("staff-token"))

    assert response.json() == {"caller": "staff"}
    assert _denials(logs) == []
