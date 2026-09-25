import tomllib
from collections.abc import Iterator, Mapping

import pytest
from fastapi.testclient import TestClient
from packaging.version import Version

from api.common.consts import PYPROJECT_PATH
from api.common.dependencies import application_information, dependency_checks
from api.common.dependency_checks import DependencyCheck
from api.gen.server.v1.health_check_connect import HealthCheckServiceASGIApplication
from api.main import app
from api.services.health_check_service import HealthCheckServiceImplementation

_RPC_PATH = "/server.v1.HealthCheckService/HealthCheck"


def _expected_version() -> str:
    with PYPROJECT_PATH.open("rb") as file:
        release = Version(tomllib.load(file)["project"]["version"]).release
    return ".".join(str(part) for part in (*release, 0, 0, 0)[:3])


async def _passing() -> bool:
    return True


async def _failing() -> bool:
    return False


async def _raising() -> bool:
    raise RuntimeError("internal detail")


@pytest.fixture
def client() -> Iterator[TestClient]:
    yield TestClient(app)
    app.dependency_overrides.clear()


def _use_checks(checks: Mapping[str, DependencyCheck]) -> None:
    app.dependency_overrides[dependency_checks] = lambda: checks


def test_health_defaults_to_plain_pass(client: TestClient) -> None:
    response = client.get("/health_check")

    assert response.status_code == 200
    assert response.text == "pass"


def test_health_full_reports_version_without_dependencies(client: TestClient) -> None:
    response = client.get("/health_check", params={"full": True})

    assert response.status_code == 200
    assert response.json() == {"status": "pass", "version": _expected_version()}


def test_health_full_with_dependencies_reports_each(client: TestClient) -> None:
    _use_checks({"database": _passing, "cache": _passing})

    response = client.get("/health_check", params={"full": True, "check_dependencies": True})

    assert response.status_code == 200
    assert response.json()["dependencies"] == {"database": "pass", "cache": "pass"}


def test_health_failing_dependency_returns_503_plain(client: TestClient) -> None:
    _use_checks({"database": _passing, "cache": _failing})

    response = client.get("/health_check", params={"check_dependencies": True})

    assert response.status_code == 503
    assert response.text == "fail"


def test_health_raising_dependency_is_reported_as_fail(client: TestClient) -> None:
    _use_checks({"database": _raising})

    response = client.get("/health_check", params={"full": True, "check_dependencies": True})

    assert response.status_code == 503
    assert response.json()["status"] == "fail"
    assert response.json()["dependencies"] == {"database": "fail"}
    assert "internal detail" not in response.text


def test_health_skips_dependencies_unless_asked(client: TestClient) -> None:
    _use_checks({"database": _failing})

    response = client.get("/health_check")

    assert response.status_code == 200


# The RPC service is not a FastAPI route, so dependency_overrides cannot reach it; these tests
# build it directly with the fake checks instead.
def _rpc_client(checks: Mapping[str, DependencyCheck]) -> TestClient:
    service = HealthCheckServiceImplementation(application_information(), checks)
    return TestClient(HealthCheckServiceASGIApplication(service))


def test_rpc_is_mounted_on_the_app(client: TestClient) -> None:
    response = client.post(_RPC_PATH, json={})

    assert response.status_code == 200
    assert response.json() == {"status": "STATUS_PASS"}


def test_rpc_defaults_to_status_only() -> None:
    response = _rpc_client({"database": _failing}).post(_RPC_PATH, json={})

    assert response.json() == {"status": "STATUS_PASS"}


def test_rpc_full_reports_version_without_dependencies() -> None:
    response = _rpc_client({"database": _passing}).post(_RPC_PATH, json={"full": True})

    assert response.json() == {"status": "STATUS_PASS", "version": _expected_version()}


def test_rpc_full_with_dependencies_reports_each() -> None:
    response = _rpc_client({"database": _passing, "cache": _passing}).post(
        _RPC_PATH, json={"full": True, "checkDependencies": True}
    )

    assert response.json()["dependencies"] == {"database": "pass", "cache": "pass"}


def test_rpc_failing_dependency_returns_fail_status() -> None:
    response = _rpc_client({"database": _passing, "cache": _failing}).post(
        _RPC_PATH, json={"checkDependencies": True}
    )

    assert response.status_code == 200
    assert response.json() == {"status": "STATUS_FAIL"}


def test_rpc_raising_dependency_is_reported_as_fail() -> None:
    response = _rpc_client({"database": _raising}).post(
        _RPC_PATH, json={"full": True, "checkDependencies": True}
    )

    assert response.json()["status"] == "STATUS_FAIL"
    assert response.json()["dependencies"] == {"database": "fail"}
    assert "internal detail" not in response.text
