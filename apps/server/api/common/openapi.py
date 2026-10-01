import json
from pathlib import Path
from typing import cast

from fastapi import FastAPI

# Written by protoc-gen-connect-openapi during server codegen, one document per .proto file.
CONNECT_OPENAPI_DIR = Path(__file__).resolve().parents[1] / "gen" / "openapi"

type JsonObject = dict[str, object]


def _object(document: JsonObject, key: str) -> JsonObject:
    return cast(JsonObject, document.setdefault(key, {}))


# Identical entries are expected: every generated document repeats the shared Connect schemas.
def _merge(target: JsonObject, source: JsonObject, section: str) -> None:
    for key, value in source.items():
        if key in target and target[key] != value:
            raise ValueError(f"OpenAPI {section} {key!r} is defined twice with different content")
        target[key] = value


def _connect_documents() -> list[JsonObject]:
    if not CONNECT_OPENAPI_DIR.is_dir():
        raise FileNotFoundError(
            f"{CONNECT_OPENAPI_DIR} is missing. Run: uv run --project apps/server "
            "python scripts/generate_proto.py buf.gen.server.yaml"
        )
    return [
        cast(JsonObject, json.loads(path.read_text(encoding="utf-8")))
        for path in sorted(CONNECT_OPENAPI_DIR.rglob("*.json"))
    ]


# ConnectRPC services are mounted ASGI apps, which FastAPI's own schema leaves out, so their
# generated documents are merged into it.
def openapi_schema(app: FastAPI) -> JsonObject:
    if app.openapi_schema is not None:
        return app.openapi_schema

    schema = cast(JsonObject, FastAPI.openapi(app))
    paths = _object(schema, "paths")
    schemas = _object(_object(schema, "components"), "schemas")
    tags = cast(list[JsonObject], schema.setdefault("tags", []))

    for document in _connect_documents():
        _merge(paths, cast(JsonObject, document.get("paths", {})), "path")
        components = cast(JsonObject, document.get("components", {}))
        _merge(schemas, cast(JsonObject, components.get("schemas", {})), "schema")
        tags.extend(
            tag for tag in cast(list[JsonObject], document.get("tags", [])) if tag not in tags
        )

    app.openapi_schema = schema
    return schema
