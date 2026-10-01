#!/usr/bin/env python3
"""Writes the server's OpenAPI spec (REST and ConnectRPC) into docs/api/ for the docs site.
--check reports stale files instead of writing them. The pre-commit hook runs this.

Usage:
    uv run --project apps/server python apps/server/export_openapi.py [--check]
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
DOCS_API = ROOT.parent.parent / "docs" / "api"

sys.path.insert(0, str(ROOT))

from api.main import app  # noqa: E402 -- needs the server directory on sys.path first


def rendered() -> dict[pathlib.Path, str]:
    spec = json.dumps(app.openapi(), indent=2, sort_keys=True, ensure_ascii=False)
    return {
        DOCS_API / "openapi.json": spec + "\n",
        # docs/api.html is opened from disk, where browsers refuse to fetch() a sibling file
        # but will load a script.
        DOCS_API / "openapi.js": f"window.OPENAPI_SPEC = {spec};\n",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    files = rendered()
    stale = [
        path
        for path, content in files.items()
        if not path.is_file() or path.read_text(encoding="utf-8") != content
    ]

    if args.check:
        for path in stale:
            print(f"stale: {path.relative_to(ROOT.parent.parent).as_posix()}")
        sys.exit(1 if stale else 0)

    DOCS_API.mkdir(parents=True, exist_ok=True)
    for path in stale:
        path.write_text(files[path], encoding="utf-8", newline="\n")
        print(f"wrote  {path.relative_to(ROOT.parent.parent).as_posix()}")


if __name__ == "__main__":
    main()
