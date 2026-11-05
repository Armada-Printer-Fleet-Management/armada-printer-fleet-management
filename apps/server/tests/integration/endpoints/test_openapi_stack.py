from fastapi.testclient import TestClient

from api.main import app


def test_the_spec_is_served_under_the_api_prefix(app_client: TestClient) -> None:
    response = app_client.get("/api/openapi.json")

    assert response.status_code == 200
    assert response.json() == app.openapi()
