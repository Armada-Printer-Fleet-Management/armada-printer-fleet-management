"""Starts and stops the integration tests' dependencies, defined in infra/test/compose.yaml."""

import os
import secrets
import shutil
import subprocess
from pathlib import Path

import pytest

COMPOSE_FILE = Path(__file__).parents[5] / "infra" / "test" / "compose.yaml"
HOST = "127.0.0.1"
# Keycloak is the slowest to become healthy, and its check allows a long start period.
WAIT_TIMEOUT_SECONDS = 300
FAILURE_LOG_LINES = 50

# These match infra/test/compose.yaml and infra/deploy/garage.toml.
DATABASE = "armada"
DATABASE_USER = "armada"
DATABASE_PORT = 5432
FILE_STORE_PORT = 3900
FILE_STORE_REGION = "garage"
FILE_STORE_BUCKET = "armada-test"
IDENTITY_PROVIDER_PORT = 8080


class DockerStack:
    """One run's dependencies. Credentials are generated per run, so a fresh clone needs no
    configuration."""

    def __init__(self) -> None:
        docker = shutil.which("docker")
        if docker is None:
            pytest.fail(
                "Integration tests need Docker, and 'docker' is not on PATH.", pytrace=False
            )
        self._docker = docker
        self._database_password = secrets.token_hex(16)
        self._file_store_access_key = "GK" + secrets.token_hex(16)
        self._file_store_secret_key = secrets.token_hex(32)
        # Compose reads every ${VAR:?} in the file for any command, including down.
        self._compose_environment = {
            **os.environ,
            "DB_PASSWORD": self._database_password,
            "GARAGE_RPC_SECRET": secrets.token_hex(32),
            "GARAGE_DEFAULT_ACCESS_KEY": self._file_store_access_key,
            "GARAGE_DEFAULT_SECRET_KEY": self._file_store_secret_key,
            "GARAGE_DEFAULT_BUCKET": FILE_STORE_BUCKET,
            "KEYCLOAK_ADMIN_USERNAME": "admin",
            "KEYCLOAK_ADMIN_PASSWORD": secrets.token_hex(16),
        }

    def start(self) -> dict[str, str]:
        """Starts the stack and returns the environment variables the server reads to use it. If
        this fails partway, stop() still cleans up."""
        # A run that was killed outright never reached its own stop().
        self.stop()

        up = self._run("up", "--wait", "--wait-timeout", str(WAIT_TIMEOUT_SECONDS))
        if up.returncode != 0:
            # Read now, because stop() removes the containers and their logs with them.
            logs = self._run("logs", "--tail", str(FAILURE_LOG_LINES))
            pytest.fail(
                f"The integration test stack did not start:\n{up.stderr}\n{logs.stdout}",
                pytrace=False,
            )
        return self._server_environment()

    def stop(self) -> None:
        self._compose("down", "--volumes", "--remove-orphans")

    def _server_environment(self) -> dict[str, str]:
        file_store = f"http://{HOST}:{self._port('garage-s3-storage', FILE_STORE_PORT)}"
        identity_provider = f"http://{HOST}:{self._port('keycloak', IDENTITY_PROVIDER_PORT)}"
        realm = f"{identity_provider}/auth/realms/armada"
        return {
            "DB_HOST": HOST,
            "DB_PORT": self._port("db", DATABASE_PORT),
            "DB_NAME": DATABASE,
            "DB_USER": DATABASE_USER,
            "DB_PASSWORD": self._database_password,
            "FILE_STORE_ENDPOINT_URL": file_store,
            "FILE_STORE_REGION": FILE_STORE_REGION,
            "FILE_STORE_BUCKET": FILE_STORE_BUCKET,
            "FILE_STORE_ACCESS_KEY": self._file_store_access_key,
            "FILE_STORE_SECRET_KEY": self._file_store_secret_key,
            "AUTH_ISSUER": realm,
            "AUTH_JWKS_URL": f"{realm}/protocol/openid-connect/certs",
        }

    def _port(self, service: str, container_port: int) -> str:
        """The random host port Docker gave a service. Compose prints it as 127.0.0.1:49153."""
        address = self._compose("port", service, str(container_port))
        return address.strip().rpartition(":")[2]

    def _compose(self, *arguments: str) -> str:
        result = self._run(*arguments)
        if result.returncode != 0:
            command = " ".join(arguments)
            pytest.fail(
                f"'docker compose {command}' failed for the integration test stack. Is Docker "
                f"running?\n{result.stderr}",
                pytrace=False,
            )
        return result.stdout

    def _run(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [self._docker, "compose", "-f", str(COMPOSE_FILE), *arguments],
            env=self._compose_environment,
            capture_output=True,
            # Windows' default encoding cannot decode everything Docker prints.
            encoding="utf-8",
            errors="replace",
            check=False,
        )
