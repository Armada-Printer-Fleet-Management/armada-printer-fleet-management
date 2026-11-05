"""Helpers for tests that call Connect services as JSON."""

from typing import Any

type Json = dict[str, Any]


def id_json(entity_id: object) -> dict[str, str]:
    """A typed ID as Connect's JSON encoding writes it."""
    return {"value": str(entity_id)}
