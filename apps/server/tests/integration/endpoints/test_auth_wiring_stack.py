"""The token check as api/main.py wires it, on the running app."""

import pytest
from fastapi.testclient import TestClient

from api.common.consts import API_PREFIX


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", f"{API_PREFIX}/health_check"),
        ("POST", f"{API_PREFIX}/server.v1.PrintJobService/ListPrintJobs"),
    ],
    ids=["REST", "Connect"],
)
def test_a_bad_authorization_header_is_a_401_on_the_app(
    app_client: TestClient, method: str, path: str
) -> None:
    response = app_client.request(
        method, path, json={}, headers={"Authorization": "Basic dXNlcjpwYXNz"}
    )

    assert response.status_code == 401
    assert response.json()["code"] == "unauthenticated"
