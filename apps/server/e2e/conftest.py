import time
from collections.abc import Iterator
from dataclasses import dataclass

import httpx2
import pytest
from proto_utils.gen.server.v1.health_check_connect import HealthCheckServiceClientSync
from proto_utils.gen.server.v1.print_job_service_connect import PrintJobServiceClientSync
from proto_utils.gen.server.v1.printer_service_connect import PrinterServiceClientSync
from pyqwest import SyncClient

from e2e.auth import BearerToken, KeycloakTokens
from e2e.settings import E2eRole, E2eSettings, load_settings

_STARTUP_TIMEOUT_S = 120.0
_POLL_INTERVAL_S = 2.0


@dataclass(frozen=True)
class SignedIn:
    """The server's Connect services, called as one test role."""

    print_jobs: PrintJobServiceClientSync
    printers: PrinterServiceClientSync


@pytest.fixture(scope="session")
def settings() -> E2eSettings:
    return load_settings()


@pytest.fixture(scope="session")
def rest(settings: E2eSettings) -> Iterator[httpx2.Client]:
    """Plain HTTP to the target, for REST routes and Keycloak, which Connect does not cover."""
    with httpx2.Client(base_url=settings.server(), timeout=httpx2.Timeout(10.0)) as client:
        yield client


@pytest.fixture(scope="session")
def connect_http() -> SyncClient:
    """One connection pool shared by every Connect client, as the desktop app does."""
    return SyncClient()


@pytest.fixture(scope="session")
def tokens(settings: E2eSettings, rest: httpx2.Client) -> KeycloakTokens:
    return KeycloakTokens(settings, rest)


# Automatic because every test needs a running server, and a stack that is still starting
# should give one clear failure here rather than a confusing one in each test.
@pytest.fixture(scope="session", autouse=True)
def server_is_up(rest: httpx2.Client) -> None:
    deadline = time.monotonic() + _STARTUP_TIMEOUT_S
    last = "no response"
    while time.monotonic() < deadline:
        try:
            response = rest.get("/api/health_check")
            if response.status_code == 200:
                return
            last = f"{response.status_code} {response.text}"
        except httpx2.HTTPError as error:
            last = repr(error)
        time.sleep(_POLL_INTERVAL_S)
    pytest.fail(f"{rest.base_url} did not become healthy in {_STARTUP_TIMEOUT_S:.0f}s: {last}")


@pytest.fixture(scope="session")
def health(settings: E2eSettings, connect_http: SyncClient) -> HealthCheckServiceClientSync:
    return HealthCheckServiceClientSync(f"{settings.server()}/api", http_client=connect_http)


def _signed_in(
    settings: E2eSettings, connect_http: SyncClient, tokens: KeycloakTokens, role: E2eRole
) -> SignedIn:
    address = f"{settings.server()}/api"
    interceptors = [BearerToken(tokens, role)]
    return SignedIn(
        print_jobs=PrintJobServiceClientSync(
            address, http_client=connect_http, interceptors=interceptors
        ),
        printers=PrinterServiceClientSync(
            address, http_client=connect_http, interceptors=interceptors
        ),
    )


@pytest.fixture(scope="session")
def as_student(settings: E2eSettings, connect_http: SyncClient, tokens: KeycloakTokens) -> SignedIn:
    return _signed_in(settings, connect_http, tokens, E2eRole.STUDENT)


@pytest.fixture(scope="session")
def as_staff(settings: E2eSettings, connect_http: SyncClient, tokens: KeycloakTokens) -> SignedIn:
    return _signed_in(settings, connect_http, tokens, E2eRole.STAFF)
