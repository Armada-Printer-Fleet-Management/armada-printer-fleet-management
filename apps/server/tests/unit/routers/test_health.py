import asyncio
import tomllib

import pytest
from packaging.version import Version

from api.common import health
from api.common.consts import PYPROJECT_PATH
from api.common.models import DependencyCheck
from tests.fake_app import FakeApp

_RPC_PATH = "/api/server.v1.HealthCheckService/HealthCheck"


def _expected_version() -> str:
    with PYPROJECT_PATH.open("rb") as file:
        release = Version(tomllib.load(file)["project"]["version"]).release
    return ".".join(str(part) for part in (*release, 0, 0, 0)[:3])


async def _pass() -> bool:
    return True


async def _fail() -> bool:
    return False


async def _raise() -> bool:
    raise RuntimeError("internal detail")


async def _hang() -> bool:
    # Never set, so this waits until the health check's timeout cancels it, with no timer here.
    await asyncio.Event().wait()
    return True


_passing = DependencyCheck(_pass)
_hanging = DependencyCheck(_hang)
_failing = DependencyCheck(_fail)
_raising = DependencyCheck(_raise)
_optional_failing = DependencyCheck(_fail, critical=False)
_optional_raising = DependencyCheck(_raise, critical=False)


def test_health_defaults_to_plain_pass(fake_app: FakeApp) -> None:
    response = fake_app(dependency_checks={"database": _passing}).get("/api/health_check")

    assert response.status_code == 200
    assert response.text == "pass"


def test_health_full_reports_version_without_dependencies(fake_app: FakeApp) -> None:
    response = fake_app(dependency_checks={"database": _passing}).get(
        "/api/health_check", params={"full": True}
    )

    assert response.status_code == 200
    assert response.json() == {"status": "pass", "version": _expected_version()}


def test_health_full_with_dependencies_reports_each(fake_app: FakeApp) -> None:
    response = fake_app(dependency_checks={"database": _passing, "cache": _passing}).get(
        "/api/health_check", params={"full": True, "check_dependencies": True}
    )

    assert response.status_code == 200
    assert response.json()["dependencies"] == {"database": "pass", "cache": "pass"}


def test_health_failing_dependency_returns_503_plain(fake_app: FakeApp) -> None:
    response = fake_app(dependency_checks={"database": _passing, "cache": _failing}).get(
        "/api/health_check", params={"check_dependencies": True}
    )

    assert response.status_code == 503
    assert response.text == "fail"


def test_health_raising_dependency_is_reported_as_fail(fake_app: FakeApp) -> None:
    response = fake_app(dependency_checks={"database": _raising}).get(
        "/api/health_check", params={"full": True, "check_dependencies": True}
    )

    assert response.status_code == 503
    assert response.json()["status"] == "fail"
    assert response.json()["dependencies"] == {"database": "fail"}
    assert "internal detail" not in response.text


def test_health_hanging_dependency_times_out_as_fail(
    fake_app: FakeApp, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(health, "DEPENDENCY_CHECK_TIMEOUT_SECONDS", 0.01)
    response = fake_app(dependency_checks={"database": _passing, "storage": _hanging}).get(
        "/api/health_check", params={"full": True, "check_dependencies": True}
    )

    assert response.status_code == 503
    assert response.json()["dependencies"] == {"database": "pass", "storage": "fail"}


def test_health_failing_optional_dependency_is_degraded(fake_app: FakeApp) -> None:
    response = fake_app(dependency_checks={"database": _passing, "metrics": _optional_failing}).get(
        "/api/health_check", params={"full": True, "check_dependencies": True}
    )

    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
    assert response.json()["dependencies"] == {"database": "pass", "metrics": "fail"}


def test_health_degraded_plain(fake_app: FakeApp) -> None:
    response = fake_app(dependency_checks={"metrics": _optional_failing}).get(
        "/api/health_check", params={"check_dependencies": True}
    )

    assert response.status_code == 200
    assert response.text == "degraded"


def test_health_raising_optional_dependency_is_degraded(fake_app: FakeApp) -> None:
    response = fake_app(dependency_checks={"metrics": _optional_raising}).get(
        "/api/health_check", params={"check_dependencies": True}
    )

    assert response.status_code == 200
    assert response.text == "degraded"


def test_health_critical_failure_outranks_degraded(fake_app: FakeApp) -> None:
    response = fake_app(dependency_checks={"database": _failing, "metrics": _optional_failing}).get(
        "/api/health_check", params={"check_dependencies": True}
    )

    assert response.status_code == 503
    assert response.text == "fail"


def test_health_skips_dependencies_unless_asked(fake_app: FakeApp) -> None:
    response = fake_app(dependency_checks={"database": _failing}).get("/api/health_check")

    assert response.status_code == 200


def test_rpc_defaults_to_status_only(fake_app: FakeApp) -> None:
    response = fake_app(dependency_checks={"database": _failing}).post(_RPC_PATH, json={})

    assert response.json() == {"status": "STATUS_PASS"}


def test_rpc_full_reports_version_without_dependencies(fake_app: FakeApp) -> None:
    response = fake_app(dependency_checks={"database": _passing}).post(
        _RPC_PATH, json={"full": True}
    )

    assert response.json() == {"status": "STATUS_PASS", "version": _expected_version()}


def test_rpc_full_with_dependencies_reports_each(fake_app: FakeApp) -> None:
    response = fake_app(dependency_checks={"database": _passing, "cache": _passing}).post(
        _RPC_PATH, json={"full": True, "checkDependencies": True}
    )

    assert response.json()["dependencies"] == {"database": "pass", "cache": "pass"}


def test_rpc_failing_dependency_returns_fail_status(fake_app: FakeApp) -> None:
    response = fake_app(dependency_checks={"database": _passing, "cache": _failing}).post(
        _RPC_PATH, json={"checkDependencies": True}
    )

    assert response.status_code == 200
    assert response.json() == {"status": "STATUS_FAIL"}


def test_rpc_raising_dependency_is_reported_as_fail(fake_app: FakeApp) -> None:
    response = fake_app(dependency_checks={"database": _raising}).post(
        _RPC_PATH, json={"full": True, "checkDependencies": True}
    )

    assert response.json()["status"] == "STATUS_FAIL"
    assert response.json()["dependencies"] == {"database": "fail"}
    assert "internal detail" not in response.text


def test_rpc_failing_optional_dependency_returns_degraded_status(fake_app: FakeApp) -> None:
    response = fake_app(
        dependency_checks={"database": _passing, "metrics": _optional_failing}
    ).post(_RPC_PATH, json={"checkDependencies": True})

    assert response.status_code == 200
    assert response.json() == {"status": "STATUS_DEGRADED"}


def test_rpc_critical_failure_outranks_degraded(fake_app: FakeApp) -> None:
    response = fake_app(
        dependency_checks={"database": _failing, "metrics": _optional_failing}
    ).post(_RPC_PATH, json={"checkDependencies": True})

    assert response.json() == {"status": "STATUS_FAIL"}
