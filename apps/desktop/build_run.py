#!/usr/bin/env python3
"""Builds the packaged desktop app: the frontend with pnpm, then the backend with PyInstaller,
which bundles the frontend build. Windows only. Works the same on a dev machine and in CI.
Output: backend/dist/<name>/<name>.exe, where <name> is the organization title in Train-Case."""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys

from _build_common import fail, resolve, run, step

ROOT = pathlib.Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend"
BACKEND = ROOT / "backend"


def executable_name() -> str:
    """The packaged name, from the backend's own reader so the spec and this script agree."""
    result = subprocess.run(
        [resolve("uv"), "run", "--project", str(BACKEND), "python", "-c",
         "from armada_runtime.packaging import executable_name; print(executable_name())"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


def check_legal_documents() -> None:
    """Fails when a legal document changed without a new effective date and SHA-256."""
    with step("Checking legal documents"):
        repository = ROOT.parents[1]
        run([sys.executable, str(repository / "scripts" / "check_legal_documents.py")], repository)


def main(dev_tools: bool = False) -> None:
    """dev_tools builds the frontend with its development-only UI, as dev_run.py runs it."""
    if sys.platform != "win32":
        fail("the desktop build is Windows only")

    # Set or cleared explicitly, so a value left in the shell cannot reach a release build.
    if dev_tools:
        os.environ["VITE_ARMADA_DEV_TOOLS"] = "1"
    else:
        os.environ.pop("VITE_ARMADA_DEV_TOOLS", None)

    check_legal_documents()

    with step("Checking generated code"):
        python_gen = ROOT.parents[1] / "packages" / "proto" / "utils" / "src" / "proto_utils" / "gen"
        for generated in (python_gen, FRONTEND / "src" / "gen"):
            if not any(path.is_file() for path in generated.rglob("*")):
                fail(
                    f"{generated} has no generated files. Run 'python scripts/generate_proto.py' "
                    "with buf.gen.python.yaml and buf.gen.desktop_ts.yaml."
                )

    with step("Building frontend"):
        run(["pnpm", "build"], cwd=FRONTEND)
        if not (FRONTEND / "dist" / "index.html").exists():
            fail("the frontend build did not produce dist/index.html")

    with step("Packaging backend"):
        run(
            ["uv", "run", "--group", "build", "pyinstaller", "--noconfirm", "desktop_backend.spec"],
            cwd=BACKEND,
        )

    with step("Verifying output"):
        name = executable_name()
        bundle = BACKEND / "dist" / name
        exe = bundle / f"{name}.exe"
        if not exe.exists():
            fail(f"packaging did not produce {exe}")
        if next(bundle.rglob("frontend/dist/index.html"), None) is None:
            fail(f"{bundle} does not contain the frontend build")

    print(f"Built {exe}", flush=True)


if __name__ == "__main__":
    main()
