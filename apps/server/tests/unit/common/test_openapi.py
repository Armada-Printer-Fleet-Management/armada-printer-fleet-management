import pytest

import export_openapi
from api.common.dependencies import application_info

# _merge is tested directly: the real spec never produces the duplicates it must handle.
from api.common.openapi import JsonObject, _merge  # pyright: ignore[reportPrivateUsage]
from api.main import app


def test_spec_covers_rest_and_connect_routes() -> None:
    paths = app.openapi()["paths"]

    assert "/api/health_check" in paths
    assert "/api/server.v1.HealthCheckService/HealthCheck" in paths


def test_spec_leaves_out_other_servers_services() -> None:
    paths = app.openapi()["paths"]

    assert not [path for path in paths if path.startswith("/printer_server.")]


def test_spec_reports_the_server_version() -> None:
    info = app.openapi()["info"]

    assert info["version"] == application_info().version_string()


def test_identical_duplicates_merge() -> None:
    target: JsonObject = {"shared": {"type": "string"}}

    _merge(target, {"shared": {"type": "string"}, "new": {}}, "schema")

    assert target == {"shared": {"type": "string"}, "new": {}}


def test_conflicting_duplicate_is_rejected() -> None:
    target: JsonObject = {"/health_check": {"get": {}}}

    with pytest.raises(ValueError, match="/health_check"):
        _merge(target, {"/health_check": {"post": {}}}, "path")


def test_published_docs_match_the_served_spec() -> None:
    stale = [
        path.name
        for path, content in export_openapi.rendered().items()
        if not path.is_file() or path.read_text(encoding="utf-8") != content
    ]

    assert not stale, (
        "docs/api is out of date; run "
        "`uv run --project apps/server python apps/server/export_openapi.py`"
    )
