"""Shared helpers for the desktop app's runner scripts (dev_run.py, build_run.py).

Output is written for two readers: a developer's terminal, and a GitHub Actions log. When
GITHUB_ACTIONS is set, steps become collapsible groups and failures become annotations."""
from __future__ import annotations

import contextlib
import os
import pathlib
import shutil
import subprocess
import sys
import time
from collections.abc import Iterator
from typing import NoReturn

IN_CI = os.environ.get("GITHUB_ACTIONS") == "true"


def fail(message: str) -> NoReturn:
    if IN_CI:
        print(f"::error::{message}", flush=True)
    else:
        print(f"error: {message}", file=sys.stderr, flush=True)
    sys.exit(1)


def resolve(tool: str) -> str:
    """finds the given tool on PATH, or exits with an error message if not found"""
    found = shutil.which(tool)
    if not found:
        fail(f"'{tool}' is not on PATH. Run /onboarding to set up your environment.")
    return found


def run(cmd: list[str], cwd: pathlib.Path) -> None:
    print(f"$ {' '.join(cmd)}  (in {cwd})", flush=True)
    subprocess.run([resolve(cmd[0]), *cmd[1:]], cwd=cwd, check=True)


@contextlib.contextmanager
def step(name: str) -> Iterator[None]:
    """Announces a step and times it. Inside CI the step's output collapses into a group."""
    print(f"::group::{name}" if IN_CI else f"==> {name}", flush=True)
    started = time.monotonic()
    succeeded = False
    try:
        yield
        succeeded = True
    finally:
        elapsed = time.monotonic() - started
        if IN_CI:
            print("::endgroup::", flush=True)
        if succeeded:
            print(f"{name}: done in {elapsed:.1f}s", flush=True)
        elif IN_CI:
            print(f"::error::{name} failed after {elapsed:.1f}s", flush=True)
        else:
            print(f"error: {name} failed after {elapsed:.1f}s", file=sys.stderr, flush=True)
