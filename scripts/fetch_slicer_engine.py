#!/usr/bin/env python3
"""Fetches the slicer engine (CuraEngine compiled to WebAssembly) into packages/slicer-engine/gen/.

Usage:
    python scripts/fetch_slicer_engine.py [--require-attestation]
    python scripts/fetch_slicer_engine.py --check

The engine is built and released by the armada-slicer-engine repository. Which release, and the
SHA-256 of every file in it, are pinned in packages/slicer-engine/engine.pin.json; to move to a new
release, change the tag and every hash there together.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import urllib.request
from typing import NoReturn

ROOT = pathlib.Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "packages" / "slicer-engine"
PIN = PACKAGE / "engine.pin.json"
GEN = PACKAGE / "gen"


def fail(message: str) -> NoReturn:
    print(f"error: {message}", file=sys.stderr, flush=True)
    sys.exit(1)


def sha256_of(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_pin() -> tuple[str, str, dict[str, str]]:
    pin = json.loads(PIN.read_text(encoding="utf-8"))
    return pin["repository"], pin["tag"], pin["assets"]


def download(url: str, destination: pathlib.Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "armada-fetch-slicer-engine"})
    with urllib.request.urlopen(request, timeout=120) as response, destination.open("wb") as out:
        shutil.copyfileobj(response, out)


def verify_attestation(path: pathlib.Path, repository: str, tag: str) -> None:
    """Checks the file was built by the engine repository's release workflow, from this tag."""
    command = [
        "gh", "attestation", "verify", str(path),
        "--repo", repository,
        "--signer-workflow", f"{repository}/.github/workflows/release.yml",
        "--source-ref", f"refs/tags/{tag}",
    ]  # fmt: skip
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        fail(
            f"{path.name} has no valid attestation from {repository}'s release workflow at {tag}.\n"
            f"{result.stderr.strip()}\n"
            "If gh is not signed in, run: gh auth login"
        )


def check() -> None:
    _, tag, assets = load_pin()
    problems = []
    for name, expected in assets.items():
        path = GEN / name
        if not path.exists():
            problems.append(f"{name} is missing")
        elif sha256_of(path) != expected:
            problems.append(f"{name} does not match its pinned SHA-256")
    if problems:
        fail(
            f"the slicer engine in {GEN.relative_to(ROOT)} is not the pinned {tag}: "
            + "; ".join(problems)
            + ". Run: python scripts/fetch_slicer_engine.py"
        )
    print(f"Slicer engine {tag} matches its pin", flush=True)


def fetch(require_attestation: bool) -> None:
    repository, tag, assets = load_pin()
    attest = shutil.which("gh") is not None
    if require_attestation and not attest:
        fail("--require-attestation needs the gh CLI")
    if not attest:
        print("gh is not installed, so attestations are not checked; SHA-256s still are.", flush=True)

    GEN.mkdir(parents=True, exist_ok=True)
    for stale in GEN.iterdir():
        if stale.name not in assets:
            stale.unlink()

    for name, expected in assets.items():
        path = GEN / name
        if path.exists() and sha256_of(path) == expected and not require_attestation:
            continue
        if not path.exists() or sha256_of(path) != expected:
            url = f"https://github.com/{repository}/releases/download/{tag}/{name}"
            print(f"Downloading {url}", flush=True)
            partial = path.with_name(f"{name}.partial")
            download(url, partial)
            digest = sha256_of(partial)
            if digest != expected:
                partial.unlink()
                fail(f"{name} checksum mismatch: expected {expected}, got {digest}. Not installed.")
            partial.replace(path)
        if attest:
            verify_attestation(path, repository, tag)
    print(f"Slicer engine {tag} fetched and verified in {GEN.relative_to(ROOT)}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch the pinned slicer engine release into packages/slicer-engine/gen/. Every file is "
            "checked against its pinned SHA-256, and against its build-provenance attestation when "
            "the gh CLI is available."
        ),
        epilog=(
            "examples:\n"
            "  python scripts/fetch_slicer_engine.py                        fetch, or do nothing if current\n"
            "  python scripts/fetch_slicer_engine.py --require-attestation  CI: attestation is mandatory\n"
            "  python scripts/fetch_slicer_engine.py --check                verify what is there; no network\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--require-attestation", action="store_true",
                      help="fail unless every file's attestation verifies (needs gh, signed in)")
    mode.add_argument("--check", action="store_true",
                      help="only check the files already fetched against the pin")
    args = parser.parse_args()

    if args.check:
        check()
    else:
        fetch(args.require_attestation)


if __name__ == "__main__":
    main()
