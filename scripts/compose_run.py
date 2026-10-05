#!/usr/bin/env python3
"""Starts or stops a whole Armada stack in Docker.

    dev     server and web with live reload, plus Postgres and Garage (infra/dev/compose.yaml)
    deploy  the deployment stack (infra/deploy/compose.yaml), from deploy images built and tagged
            here, since no image registry is published yet

Settings live in config/compose.<stack>.env, which is gitignored. A missing or placeholder secret
is generated on first run and never replaced afterwards, since regenerating one would lock the
stack out of its own database and stored files. The deploy stack also needs a domain and an
administrator email, given as flags once and kept in the file.

Usage:
    python scripts/compose_run.py dev [up|down]
    python scripts/compose_run.py deploy [up|down] [--domain <domain>] [--admin-email <email>]
Examples:
    python scripts/compose_run.py dev
    python scripts/compose_run.py deploy --domain :80 --admin-email admin@localhost
"""

from __future__ import annotations

import argparse
import pathlib
import secrets
import shutil
import subprocess
import sys
from collections.abc import Callable

REPO = pathlib.Path(__file__).resolve().parent.parent
CONFIG = REPO / "config"
COMPOSE_FILES = {
    "dev": REPO / "infra" / "dev" / "compose.yaml",
    "deploy": REPO / "infra" / "deploy" / "compose.yaml",
}
DEPLOY_IMAGES = {
    "armada-server": REPO / "apps" / "server" / "deploy.Dockerfile",
    "armada-web": REPO / "apps" / "web" / "deploy.Dockerfile",
}
DEV_GENERATED = [
    REPO / "apps" / "server" / "api" / "gen",
    REPO / "apps" / "web" / "src" / "gen",
]
PLACEHOLDER = "REPLACE_ME"

# Garage's documented formats: the RPC secret is 32 random bytes as hex, and its quick start
# generates the default access key as GK plus 16 random bytes as hex, with a 32-byte secret key.
GENERATED: dict[str, Callable[[], str]] = {
    "DB_PASSWORD": lambda: secrets.token_hex(16),
    "GARAGE_RPC_SECRET": lambda: secrets.token_hex(32),
    "GARAGE_DEFAULT_ACCESS_KEY": lambda: "GK" + secrets.token_hex(16),
    "GARAGE_DEFAULT_SECRET_KEY": lambda: secrets.token_hex(32),
}
DEFAULTS = {"GARAGE_DEFAULT_BUCKET": "armada"}
DEPLOY_DEFAULTS = {"GHCR_OWNER": "local", "VERSION": "dev"}


def resolve(tool: str) -> str:
    """finds the given tool on PATH, or exits with an error message if not found"""
    found = shutil.which(tool)
    if not found:
        sys.exit(
            f"'{tool}' is not on PATH. Run /onboarding to set up your environment."
        )
    return found


def read_env(path: pathlib.Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            key, sep, value = line.partition("=")
            if sep and not line.lstrip().startswith("#"):
                values[key.strip()] = value.strip()
    return values


def write_env(path: pathlib.Path, updates: dict[str, str]) -> None:
    """Sets the given keys in an env file, keeping every other line and comment as it was."""
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    pending = dict(updates)
    for i, line in enumerate(lines):
        key = line.partition("=")[0].strip()
        if key in pending and not line.lstrip().startswith("#"):
            lines[i] = f"{key}={pending.pop(key)}"
    lines += [f"{key}={value}" for key, value in pending.items()]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def prepare_env(
    stack: str, domain: str | None, admin_email: str | None
) -> pathlib.Path:
    path = CONFIG / f"compose.{stack}.env"
    current = read_env(path)

    def unset(key: str) -> bool:
        return current.get(key, "") in ("", PLACEHOLDER)

    updates = {key: make() for key, make in GENERATED.items() if unset(key)}
    defaults = DEFAULTS | (DEPLOY_DEFAULTS if stack == "deploy" else {})
    updates |= {key: value for key, value in defaults.items() if unset(key)}
    if domain is not None:
        updates["DOMAIN"] = domain
    if admin_email is not None:
        updates["ADMIN_EMAIL"] = admin_email
    if updates:
        write_env(path, updates)

    if stack == "deploy":
        merged = current | updates
        missing = [
            key
            for key in ("DOMAIN", "ADMIN_EMAIL")
            if merged.get(key, "") in ("", PLACEHOLDER)
        ]
        if missing:
            sys.exit(
                f"{', '.join(missing)} not set in {path.relative_to(REPO).as_posix()}. Pass "
                "--domain and --admin-email once (--domain :80 serves plain HTTP for a test machine)."
            )
    return path


def build_deploy_images(env: dict[str, str]) -> None:
    docker = resolve("docker")
    for name, dockerfile in DEPLOY_IMAGES.items():
        tag = f"ghcr.io/{env['GHCR_OWNER']}/{name}:{env['VERSION']}"
        print(f"Building {tag}", flush=True)
        subprocess.run(
            [docker, "build", "-f", str(dockerfile), "-t", tag, str(REPO)], check=True
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Start or stop a whole Armada stack in Docker."
    )
    parser.add_argument("stack", choices=sorted(COMPOSE_FILES))
    parser.add_argument("action", nargs="?", choices=["up", "down"], default="up")
    parser.add_argument("--domain", help="deploy only: the site address Caddy serves")
    parser.add_argument(
        "--admin-email", help="deploy only: the certificate contact address"
    )
    args = parser.parse_args()

    if args.stack == "dev" and (args.domain or args.admin_email):
        parser.error("--domain and --admin-email apply to the deploy stack only")

    env_file = prepare_env(args.stack, args.domain, args.admin_email)
    compose = [
        resolve("docker"), "compose",
        "-f", str(COMPOSE_FILES[args.stack]),
        "--env-file", str(env_file),
    ]  # fmt: skip

    if args.action == "down":
        # Never -v: that deletes the database, the stored files and Caddy's certificates.
        command = [*compose, "down"]
    elif args.stack == "dev":
        missing = [
            p.relative_to(REPO).as_posix() for p in DEV_GENERATED if not p.is_dir()
        ]
        if missing:
            sys.exit(
                f"{', '.join(missing)} missing. Run /onboarding to generate the API code."
            )
        command = [*compose, "up", "--build", "--watch"]
    else:
        command = [*compose, "up", "--detach", "--wait"]

    try:
        if args.stack == "deploy" and args.action == "up":
            build_deploy_images(read_env(env_file))
        sys.exit(subprocess.run(command, cwd=REPO, check=False).returncode)
    except subprocess.CalledProcessError as error:
        sys.exit(error.returncode)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
