#!/usr/bin/env python3
"""Installs NSIS, the tool that builds the desktop app's Windows installer. Windows only.

Usage:
    python scripts/install_nsis.py [--force]

To move to a new NSIS version, change VERSION and SHA256 together.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from typing import NoReturn

VERSION = "3.12"
URL = "https://sourceforge.net/projects/nsis/files/NSIS%203/3.12/nsis-3.12-setup.exe/download"
SHA256 = "3bc2b06253a7e4957111be152ac6a536e0c7478a706e19da814038db5d706495"

INSTALL_DIR = pathlib.Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "NSIS"


def fail(message: str) -> NoReturn:
    print(f"error: {message}", file=sys.stderr, flush=True)
    sys.exit(1)


def installed_version() -> str | None:
    makensis = shutil.which("makensis") or str(INSTALL_DIR / "makensis.exe")
    if not pathlib.Path(makensis).exists():
        return None
    result = subprocess.run([makensis, "/VERSION"], capture_output=True, text=True, check=False)
    return result.stdout.strip().removeprefix("v") or None


def download(destination: pathlib.Path) -> None:
    print(f"Downloading {URL}", flush=True)
    with urllib.request.urlopen(URL, timeout=120) as response, destination.open("wb") as out:
        shutil.copyfileobj(response, out)
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    if digest != SHA256:
        fail(f"NSIS {VERSION} checksum mismatch: expected {SHA256}, got {digest}. Not installing.")
    print(f"Checksum verified ({digest})", flush=True)


def install(setup: pathlib.Path) -> None:
    # Start-Process -Verb RunAs raises the UAC prompt the setup program needs; calling it
    # directly from an unelevated process fails instead of prompting.
    quoted = str(setup).replace("'", "''")
    command = (
        f"$p = Start-Process -FilePath '{quoted}' -ArgumentList '/S' -Verb RunAs -Wait -PassThru; "
        "exit $p.ExitCode"
    )
    result = subprocess.run(["powershell", "-NoProfile", "-Command", command], check=False)
    if result.returncode != 0:
        fail(f"the NSIS setup program exited with code {result.returncode}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            f"Install NSIS {VERSION}, which builds the desktop app's Windows installer. "
            "Windows only. Downloads the official setup program, confirms it against the pinned "
            f"checksum, and installs it silently to {INSTALL_DIR}. "
            "Windows shows one administrator (UAC) prompt; CI runners are already elevated."
        ),
        epilog=(
            "examples:\n"
            "  python scripts/install_nsis.py          install, or do nothing if already present\n"
            "  python scripts/install_nsis.py --force  replace a different installed version\n"
            "\n"
            f"Does nothing if NSIS {VERSION} is already installed, and leaves a different "
            "version alone\nunless --force is given. In GitHub Actions it also adds the NSIS "
            "folder to PATH\nfor later steps."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--force", action="store_true",
                        help=f"install {VERSION} even if another NSIS version is present")
    args = parser.parse_args()

    if sys.platform != "win32":
        fail("NSIS is only needed to build the Windows installer")

    current = installed_version()
    if current == VERSION and not args.force:
        print(f"NSIS {VERSION} is already installed", flush=True)
    elif current is not None and not args.force:
        print(
            f"NSIS {current} is installed, but this project pins {VERSION}. "
            "Leaving it alone; re-run with --force to replace it.",
            flush=True,
        )
    else:
        if os.environ.get("GITHUB_ACTIONS") != "true":
            print("Windows will ask for administrator rights to install NSIS.", flush=True)
        with tempfile.TemporaryDirectory() as temp:
            setup = pathlib.Path(temp) / f"nsis-{VERSION}-setup.exe"
            download(setup)
            install(setup)
        if installed_version() != VERSION:
            fail(f"NSIS {VERSION} did not install to {INSTALL_DIR}")
        print(f"Installed NSIS {VERSION} to {INSTALL_DIR}", flush=True)

    github_path = os.environ.get("GITHUB_PATH")
    if github_path:
        with open(github_path, "a", encoding="utf-8") as f:
            f.write(f"{INSTALL_DIR}\n")


if __name__ == "__main__":
    main()