#!/usr/bin/env python3
"""Runs the desktop app. Default mode builds the frontend and launches the
backend against the built output -- the closest thing to the installed app.
--dev launches a hot-reloading Vite server instead."""
from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys

from _build_common import resolve, run

ROOT = pathlib.Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend"
BACKEND = ROOT / "backend"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dev", action="store_true")
    args = parser.parse_args()

    if args.dev:
        dev_server = subprocess.Popen([resolve("pnpm"), "dev"], cwd=FRONTEND)
        try:
            run(
                ["uv", "run", "--project", str(BACKEND), "desktop-backend",
                 "--target", "http://localhost:5173"],
                cwd=ROOT,
            )
        finally:
            dev_server.terminate()
    else:
        run(["pnpm", "build"], cwd=FRONTEND)
        index_html = FRONTEND / "dist" / "index.html"
        if not index_html.exists():
            sys.exit(f"build did not produce {index_html}")
        run(
            ["uv", "run", "--project", str(BACKEND), "desktop-backend",
             "--target", index_html.as_uri()],
            cwd=ROOT,
        )


if __name__ == "__main__":
    main()