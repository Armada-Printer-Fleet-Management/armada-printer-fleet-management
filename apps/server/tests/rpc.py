"""Helpers for tests that call Connect services as JSON."""

from typing import Any

from fastapi.testclient import TestClient

# Decoded JSON is indexed freely by the tests, which a precise recursive type would refuse.
type Json = dict[str, Any]


def id_json(entity_id: object) -> dict[str, str]:
    """A typed ID as Connect's JSON encoding writes it."""
    return {"value": str(entity_id)}


def post(client: TestClient, path: str, body: Json, expect: int = 200) -> Json:
    """Calls one RPC and checks its status, returning the decoded body."""
    response = client.post(path, json=body)
    assert response.status_code == expect, response.text
    result: Json = response.json()
    return result
