import pkgutil
from importlib import import_module

import proto_utils.gen.server.v1 as server_v1
import pytest
from fastapi.routing import APIRoute
from starlette.routing import Route

from api.common.access_policy import ACCESS, PUBLIC, STAFF, AccessPolicy, Decision, Endpoint
from api.common.authentication import Caller, Role
from api.common.consts import API_PREFIX
from api.main import app

STUDENT = Caller("student", frozenset({Role.STUDENT}))
STAFF_MEMBER = Caller("staff", frozenset({Role.STAFF}))
ADMIN = Caller("admin", frozenset({Role.ADMIN}))
GUEST = Caller("guest", frozenset({Role.GUEST}))
EVERY_ROLE = Caller("everyone", frozenset(Role))

FILE_PATH = f"{API_PREFIX}/files/00000000-0000-4000-8000-000000000201"


def rpc(service: str, method: str) -> str:
    return f"{API_PREFIX}/server.v1.{service}/{method}"


# Decisions per caller


SMALL_TABLE = AccessPolicy(
    {
        Endpoint("GET", "/public"): PUBLIC,
        Endpoint("GET", "/staff"): STAFF,
    }
)


@pytest.mark.parametrize("caller", [None, GUEST, STAFF_MEMBER], ids=["no caller", "guest", "staff"])
def test_a_public_endpoint_allows_anyone(caller: Caller | None) -> None:
    assert SMALL_TABLE.decide("GET", "/public", caller) == Decision.ALLOW


@pytest.mark.parametrize(
    ("caller", "decision"),
    [
        (None, Decision.UNAUTHENTICATED),
        (STUDENT, Decision.FORBIDDEN),
        (STAFF_MEMBER, Decision.ALLOW),
    ],
    ids=["no caller", "role not allowed", "role allowed"],
)
def test_a_protected_endpoint_decides_by_the_callers_roles(
    caller: Caller | None, decision: Decision
) -> None:
    assert SMALL_TABLE.decide("GET", "/staff", caller) == decision


# The project's role rules, against the real table

ALLOWED = Decision.ALLOW
FORBIDDEN = Decision.FORBIDDEN


@pytest.mark.parametrize(
    ("method", "path", "student", "staff", "admin", "guest"),
    [
        ("POST", rpc("PrintJobService", "CreatePrintJob"), ALLOWED, ALLOWED, ALLOWED, FORBIDDEN),
        ("POST", rpc("PrintJobService", "SubmitPrintJob"), ALLOWED, ALLOWED, ALLOWED, FORBIDDEN),
        (
            "POST",
            rpc("PrintJobService", "TransitionPrintJob"),
            FORBIDDEN,
            ALLOWED,
            ALLOWED,
            FORBIDDEN,
        ),
        ("POST", rpc("FileService", "GetFile"), ALLOWED, ALLOWED, ALLOWED, FORBIDDEN),
        ("PUT", FILE_PATH, ALLOWED, ALLOWED, ALLOWED, FORBIDDEN),
        ("GET", FILE_PATH, ALLOWED, ALLOWED, ALLOWED, FORBIDDEN),
        ("DELETE", FILE_PATH, ALLOWED, ALLOWED, ALLOWED, FORBIDDEN),
        (
            "POST",
            rpc("PrinterService", "TransitionPrinter"),
            FORBIDDEN,
            ALLOWED,
            ALLOWED,
            FORBIDDEN,
        ),
        (
            "POST",
            rpc("PrinterQueueService", "ListPrinterQueues"),
            FORBIDDEN,
            ALLOWED,
            ALLOWED,
            FORBIDDEN,
        ),
        ("GET", f"{API_PREFIX}/health_check", ALLOWED, ALLOWED, ALLOWED, ALLOWED),
        ("POST", rpc("HealthCheckService", "HealthCheck"), ALLOWED, ALLOWED, ALLOWED, ALLOWED),
    ],
)
def test_each_role_reaches_only_its_endpoints(
    method: str,
    path: str,
    student: Decision,
    staff: Decision,
    admin: Decision,
    guest: Decision,
) -> None:
    policy = AccessPolicy(ACCESS)

    assert [
        policy.decide(method, path, caller) for caller in (STUDENT, STAFF_MEMBER, ADMIN, GUEST)
    ] == [
        student,
        staff,
        admin,
        guest,
    ]


# Specificity and defaults


@pytest.mark.parametrize("specific_first", [True, False], ids=["specific first", "specific last"])
def test_a_specific_row_overrides_its_service_wherever_it_is(specific_first: bool) -> None:
    rows = [
        (Endpoint("POST", "/svc/Special"), STAFF),
        (Endpoint("POST", "/svc/{procedure}"), PUBLIC),
    ]
    policy = AccessPolicy(dict(rows if specific_first else reversed(rows)))

    assert policy.decide("POST", "/svc/Special", None) == Decision.UNAUTHENTICATED
    assert policy.decide("POST", "/svc/Other", None) == Decision.ALLOW


def test_an_unlisted_endpoint_allows_no_role() -> None:
    assert SMALL_TABLE.decide("GET", "/unlisted", EVERY_ROLE) == Decision.FORBIDDEN


def test_head_follows_the_get_rule() -> None:
    assert SMALL_TABLE.decide("HEAD", "/staff", STUDENT) == Decision.FORBIDDEN
    assert SMALL_TABLE.decide("HEAD", "/public", None) == Decision.ALLOW


# Every endpoint is listed


def _rest_endpoints() -> list[tuple[str, str]]:
    return [
        (method, route.path)
        for route in app.routes
        if isinstance(route, APIRoute | Route)
        for method in sorted(route.methods or ())
        if method != "HEAD"
    ]


def _rpc_endpoints() -> list[tuple[str, str]]:
    endpoints: list[tuple[str, str]] = []
    for module in pkgutil.iter_modules(server_v1.__path__):
        if module.name.endswith("_pb2"):
            descriptor = import_module(f"{server_v1.__name__}.{module.name}").DESCRIPTOR
            for service in descriptor.services_by_name.values():
                endpoints += [
                    ("POST", f"{API_PREFIX}/{service.full_name}/{method.name}")
                    for method in service.methods
                ]
    return endpoints


def test_every_endpoint_of_the_app_is_in_the_table() -> None:
    policy = AccessPolicy(ACCESS)
    endpoints = _rest_endpoints() + _rpc_endpoints()

    unlisted = [
        f"{method} {path}"
        for method, path in endpoints
        if policy.decide(method, path, EVERY_ROLE) != Decision.ALLOW
    ]

    assert len(_rpc_endpoints()) > 0
    assert unlisted == [], "add these to ACCESS in api/common/access_policy.py"
