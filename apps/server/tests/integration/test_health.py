import tomllib

from fastapi.testclient import TestClient
from packaging.version import Version

from api.common.consts import PYPROJECT_PATH
from api.main import app


def test_health_reports_status_and_version() -> None:
    with PYPROJECT_PATH.open("rb") as file:
        release = Version(tomllib.load(file)["project"]["version"]).release
    expected = ".".join(str(part) for part in (*release, 0, 0, 0)[:3])

    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": expected}
