from typing import cast

import pytest
from fastapi import FastAPI
from proto_utils.gen.server.v1.health_check_connect import HealthCheckServiceASGIApplication

import export_openapi
from api.common.consts import API_PREFIX
from api.common.dependencies import application_info

# _merge is tested directly: the real spec never produces the duplicates it must handle.
from api.common.openapi import (
    JsonObject,
    _merge,  # pyright: ignore[reportPrivateUsage]
    openapi_schema,
)
from api.main import app
from api.services.health_check_service import HealthCheckServiceImplementation
from api.services.mount import mount_rpc


def test_spec_covers_rest_and_connect_routes() -> None:
    paths = app.openapi()["paths"]

    assert f"{API_PREFIX}/health_check" in paths
    assert f"{API_PREFIX}/server.v1.HealthCheckService/HealthCheck" in paths


def test_spec_leaves_out_other_servers_services() -> None:
    paths = app.openapi()["paths"]

    assert not [path for path in paths if path.startswith("/printer_server.")]


def test_spec_reports_the_server_version() -> None:
    info = app.openapi()["info"]

    assert info["version"] == application_info().version_string()


def test_spec_leaves_out_services_the_app_does_not_mount() -> None:
    health_only = FastAPI()
    health_check = HealthCheckServiceImplementation(application_info(), {})
    mount_rpc(health_only, HealthCheckServiceASGIApplication(health_check))

    spec = openapi_schema(health_only)

    paths = cast(JsonObject, spec["paths"])
    schemas = cast(JsonObject, cast(JsonObject, spec["components"])["schemas"])
    tags = cast(list[JsonObject], spec["tags"])
    assert not [path for path in paths if path.startswith(f"{API_PREFIX}/server.v1.UserService/")]
    assert "server.v1.GetUserRequest" not in schemas
    assert "server.v1.UserService" not in [tag["name"] for tag in tags]


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
