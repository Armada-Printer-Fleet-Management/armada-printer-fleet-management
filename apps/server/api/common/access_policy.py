"""Which roles may call each endpoint. The authentication middleware checks every request against
ACCESS, so every endpoint must be listed: one that is not allows no role."""

import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from starlette.routing import compile_path

from api.common.authentication import Caller, Role
from api.common.consts import API_PREFIX, FILES_PATH


@dataclass(frozen=True)
class Endpoint:
    """A method and a path template, such as /api/files/{file_id}."""

    method: str
    path: str


class Decision(StrEnum):
    ALLOW = "allow"
    UNAUTHENTICATED = "unauthenticated"
    FORBIDDEN = "forbidden"


# None marks an endpoint that needs no sign-in.
type Allowed = frozenset[Role] | None

PUBLIC: Allowed = None
STAFF = frozenset({Role.STAFF, Role.ADMIN})
STUDENTS_AND_STAFF = STAFF | {Role.STUDENT}


def rpc_service(service: str) -> Endpoint:
    """Every procedure of a Connect service: each is POST /api/<package>.<Service>/<Method>."""
    return Endpoint("POST", f"{API_PREFIX}/server.v1.{service}/{{procedure}}")


ACCESS: Mapping[Endpoint, Allowed] = {
    Endpoint("GET", f"{API_PREFIX}/health_check"): PUBLIC,
    rpc_service("HealthCheckService"): PUBLIC,
    Endpoint("GET", f"{API_PREFIX}/docs"): PUBLIC,
    # FastAPI serves Swagger's sign-in redirect outside the API prefix.
    Endpoint("GET", "/docs/oauth2-redirect"): PUBLIC,
    Endpoint("GET", f"{API_PREFIX}/redoc"): PUBLIC,
    Endpoint("GET", f"{API_PREFIX}/openapi.json"): PUBLIC,
    rpc_service("PrintJobService"): STUDENTS_AND_STAFF,
    # Every transition is a staff action; students submit through SubmitPrintJob.
    Endpoint("POST", f"{API_PREFIX}/server.v1.PrintJobService/TransitionPrintJob"): STAFF,
    rpc_service("FileService"): STUDENTS_AND_STAFF,
    rpc_service("PrinterService"): STAFF,
    rpc_service("PrinterQueueService"): STAFF,
    Endpoint("PUT", f"{API_PREFIX}{FILES_PATH}/{{file_id}}"): STUDENTS_AND_STAFF,
    Endpoint("GET", f"{API_PREFIX}{FILES_PATH}/{{file_id}}"): STUDENTS_AND_STAFF,
    Endpoint("DELETE", f"{API_PREFIX}{FILES_PATH}/{{file_id}}"): STUDENTS_AND_STAFF,
}


def _parameters(endpoint: Endpoint) -> int:
    return len(compile_path(endpoint.path)[2])


class AccessPolicy:
    """Decides each request against a table. When several rows match, the most specific wins,
    the one with fewest path parameters, so a single procedure can override its whole service
    wherever it appears in the table."""

    def __init__(self, access: Mapping[Endpoint, Allowed]) -> None:
        # Compiled once: the middleware runs before routing, so it matches the templates itself.
        self._rules: list[tuple[str, re.Pattern[str], Allowed]] = [
            (endpoint.method, compile_path(endpoint.path)[0], allowed)
            for endpoint, allowed in sorted(access.items(), key=lambda row: _parameters(row[0]))
        ]

    def _allowed(self, method: str, path: str) -> Allowed:
        # Starlette answers HEAD on every GET route.
        method = "GET" if method == "HEAD" else method
        for rule_method, pattern, allowed in self._rules:
            if rule_method == method and pattern.match(path):
                return allowed
        return frozenset()

    def decide(self, method: str, path: str, caller: Caller | None) -> Decision:
        allowed = self._allowed(method, path)
        if allowed is None:
            return Decision.ALLOW
        if caller is None:
            return Decision.UNAUTHENTICATED
        if caller.roles & allowed:
            return Decision.ALLOW
        return Decision.FORBIDDEN
