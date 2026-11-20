#!/usr/bin/env python3
"""Runs `buf generate` for one template, optionally adding a local npm
plugin's bin directory to PATH first. onboarding, CI, pre-push, and app runner scripts all call
this instead of duplicating it.

*Note: for using this script, you may need to run it with the uv environment of the target service you're trying to generate protos for.  See examples

Usage:
    python scripts/generate_proto.py <template> [--node-modules <dir>]
    python scripts/generate_proto.py --all
Examples:
    uv run --project packages/proto/utils python scripts/generate_proto.py buf.gen.python.yaml
    uv run --project apps/server python scripts/generate_proto.py buf.gen.server.yaml
    python scripts/generate_proto.py buf.gen.desktop_ts.yaml --node-modules apps/desktop/frontend/node_modules
"""
from __future__ import annotations

import argparse
import os
import pathlib
import re
import subprocess
import sys

_OUT = re.compile(r"^\s*out:\s*(\S+)", re.MULTILINE)
_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPT = pathlib.Path(__file__).resolve()

# Every template, with the environment it needs: a uv project whose plugins buf runs, or the
# node_modules holding its npm plugin. Python's shared output goes first; the others import it.
_ALL: list[tuple[str, list[str]]] = [
    ("buf.gen.python.yaml", ["uv", "run", "--project", "packages/proto/utils", "python"]),
    ("buf.gen.server.yaml", ["uv", "run", "--project", "apps/server", "python"]),
    ("buf.gen.desktop_ts.yaml", [sys.executable]),
    ("buf.gen.web_ts.yaml", [sys.executable]),
    ("buf.gen.slicer_ts.yaml", [sys.executable]),
]
_NODE_MODULES = {
    "buf.gen.desktop_ts.yaml": "apps/desktop/frontend/node_modules",
    "buf.gen.web_ts.yaml": "apps/web/node_modules",
    "buf.gen.slicer_ts.yaml": "packages/slicer/node_modules",
}


def make_python_package(out_dir: pathlib.Path) -> None:
    """Makes protoc's Python output importable as a subpackage (proto_utils.gen). protoc imports
    sibling files absolutely (`from common.v1 import ...`), which only resolves with the output
    directory itself on sys.path, so those imports are rewritten relative. It also writes no
    __init__.py, and pyright does not resolve namespace packages inside an installed package."""
    packages = {p.name for p in out_dir.iterdir() if p.is_dir() and p.name != "__pycache__"}
    if not packages:
        return
    for directory in [out_dir, *(p for p in out_dir.rglob("*") if p.is_dir())]:
        if directory.name != "__pycache__":
            (directory / "__init__.py").touch()
    absolute = re.compile(rf"^from ((?:{'|'.join(map(re.escape, packages))})\.)", re.MULTILINE)
    for path in [*out_dir.rglob("*.py"), *out_dir.rglob("*.pyi")]:
        dots = "." * len(path.relative_to(out_dir).parts)
        text = path.read_text(encoding="utf-8")
        rewritten = absolute.sub(rf"from {dots}\1", text)
        if rewritten != text:
            path.write_text(rewritten, encoding="utf-8")


def generate_all() -> None:
    """Runs this script once per template, each in the environment it needs. A TypeScript
    template whose node_modules is not installed is skipped, as onboarding does."""
    for template, interpreter in _ALL:
        command = [*interpreter, str(_SCRIPT), template]
        node_modules = _NODE_MODULES.get(template)
        if node_modules:
            if not (_ROOT / node_modules).is_dir():
                print(f"skipped  {template}: {node_modules} is missing; run pnpm install")
                continue
            command += ["--node-modules", node_modules]
        print(f"generate {template}", flush=True)
        subprocess.run(command, check=True, cwd=_ROOT)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("template", nargs="?", help="e.g. buf.gen.python.yaml")
    parser.add_argument("--node-modules", help="dir whose .bin/ is prepended to PATH")
    parser.add_argument("--all", action="store_true", help="generate every template")
    args = parser.parse_args()

    if args.all:
        if args.template or args.node_modules:
            parser.error("--all takes no template or --node-modules")
        generate_all()
        return
    if not args.template:
        parser.error("give a template, or --all")

    env = os.environ.copy()
    if args.node_modules:
        bin_dir = pathlib.Path(args.node_modules) / ".bin"
        env["PATH"] = f"{bin_dir}{os.pathsep}{env.get('PATH', '')}"

    subprocess.run(["buf", "generate", "--template", args.template], check=True, env=env)

    # Only Python output needs packaging; TypeScript output has no _pb2 files and is skipped.
    template = pathlib.Path(args.template).read_text(encoding="utf-8")
    for out in {pathlib.Path(match) for match in _OUT.findall(template)}:
        if out.is_dir() and any(out.rglob("*_pb2.py")):
            make_python_package(out)


if __name__ == "__main__":
    main()