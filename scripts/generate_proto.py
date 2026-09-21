#!/usr/bin/env python3
"""Runs `buf generate` for one template, optionally adding a local npm
plugin's bin directory to PATH first. onboarding, CI, pre-push, and app runner scripts all call
this instead of duplicating it."""
from __future__ import annotations

import argparse
import os
import pathlib
import subprocess


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("template", help="e.g. buf.gen.desktop_python.yaml")
    parser.add_argument("--node-modules", help="dir whose .bin/ is prepended to PATH")
    args = parser.parse_args()

    env = os.environ.copy()
    if args.node_modules:
        bin_dir = pathlib.Path(args.node_modules) / ".bin"
        env["PATH"] = f"{bin_dir}{os.pathsep}{env.get('PATH', '')}"

    subprocess.run(["buf", "generate", "--template", args.template], check=True, env=env)


if __name__ == "__main__":
    main()