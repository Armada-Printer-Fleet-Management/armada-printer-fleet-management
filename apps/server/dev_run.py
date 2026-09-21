#!/usr/bin/env python3
"""Runs the server locally on uvicorn. Default mode serves api.main:app as is.
--dev reloads on changes under api/ instead, for active development."""

from __future__ import annotations

import argparse
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent


def resolve(tool: str) -> str:
    """finds the given tool on PATH, or exits with an error message if not found"""
    found = shutil.which(tool)
    if not found:
        sys.exit(f"'{tool}' is not on PATH. Run /onboarding to set up your environment.")
    return found


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dev", action="store_true")
    args = parser.parse_args()

    if not (ROOT / "api" / "gen").is_dir():
        sys.exit("api/gen is missing. Run /onboarding to generate the API code.")

    cmd = [resolve("uv"), "run", "uvicorn", "api.main:app"]
    if args.dev:
        cmd += ["--reload", "--reload-dir", "api"]

    try:
        sys.exit(subprocess.run(cmd, cwd=ROOT).returncode)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
