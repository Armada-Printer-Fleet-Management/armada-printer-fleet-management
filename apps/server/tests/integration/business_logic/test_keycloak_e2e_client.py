"""e2e/keycloak-e2e-client.sh against the stack's Keycloak, which imports the shipped realm: the
client it creates is the one the e2e suite signs in through."""

import base64
import json
import secrets
from dataclasses import dataclass
from pathlib import Path

import httpx2
import pytest

from tests.integration.utils.docker_stack import DockerStack

APP = Path(__file__).parents[3]
CLIENT_SCRIPT = APP / "e2e" / "keycloak-e2e-client.sh"
USERS_SCRIPT = APP.parents[1] / "infra" / "dev" / "keycloak-dev-users.sh"
CLIENT_ID = "armada-e2e"
USERNAME = "student"


@dataclass(frozen=True)
class Provisioned:
    client_secret: str
    user_password: str
    script_environment: dict[str, str]


def _run(stack: DockerStack, script: Path, environment: dict[str, str]) -> str:
    result = stack.run_script("keycloak", script, environment)
    assert result.returncode == 0, f"{script.name} failed:\n{result.stdout}\n{result.stderr}"
    return result.stdout


@pytest.fixture(scope="module")
def provisioned(docker_stack: DockerStack) -> Provisioned:
    """Runs the client script, and the dev users script for a user to sign in as, as e2e.ci.yml
    does."""
    admin_username, admin_password = docker_stack.identity_provider_admin()
    client_secret = secrets.token_hex(32)
    user_password = secrets.token_hex(16)
    environment = {
        "KEYCLOAK_ADMIN_USERNAME": admin_username,
        "KEYCLOAK_ADMIN_PASSWORD": admin_password,
        "E2E_AUTH_CLIENT_SECRET": client_secret,
        "DEV_USER_PASSWORD": user_password,
    }
    _run(docker_stack, CLIENT_SCRIPT, environment)
    _run(docker_stack, USERS_SCRIPT, environment)
    return Provisioned(client_secret, user_password, environment)


def _password_grant(
    stack_environment: dict[str, str], provisioned: Provisioned, client_secret: str
) -> httpx2.Response:
    return httpx2.post(
        f"{stack_environment['AUTH_ISSUER']}/protocol/openid-connect/token",
        data={
            "grant_type": "password",
            "client_id": CLIENT_ID,
            "client_secret": client_secret,
            "username": USERNAME,
            "password": provisioned.user_password,
        },
        timeout=10.0,
    )


def _claims(access_token: str) -> dict[str, object]:
    payload = access_token.split(".")[1]
    # JWTs drop base64 padding; decoding needs it back.
    padded = payload + "=" * (-len(payload) % 4)
    decoded: dict[str, object] = json.loads(base64.urlsafe_b64decode(padded))
    return decoded


def test_a_test_user_signs_in_through_the_client(
    stack_environment: dict[str, str], provisioned: Provisioned
) -> None:
    response = _password_grant(stack_environment, provisioned, provisioned.client_secret)

    assert response.status_code == 200, response.text
    assert response.json()["access_token"]


def test_its_access_tokens_name_the_server_as_audience(
    stack_environment: dict[str, str], provisioned: Provisioned
) -> None:
    response = _password_grant(stack_environment, provisioned, provisioned.client_secret)

    audience = _claims(response.json()["access_token"])["aud"]
    # Keycloak writes a single audience as a string and several as a list.
    assert "armada-server" in (audience if isinstance(audience, list) else [audience])


def test_a_wrong_client_secret_is_refused(
    stack_environment: dict[str, str], provisioned: Provisioned
) -> None:
    response = _password_grant(stack_environment, provisioned, secrets.token_hex(32))

    assert response.status_code == 401
    # Keycloak's code for bad client credentials, where RFC 6749 names invalid_client.
    assert response.json()["error"] == "unauthorized_client"


def test_running_it_again_leaves_the_client_as_it_was(
    docker_stack: DockerStack, stack_environment: dict[str, str], provisioned: Provisioned
) -> None:
    again = {**provisioned.script_environment, "E2E_AUTH_CLIENT_SECRET": secrets.token_hex(32)}

    output = _run(docker_stack, CLIENT_SCRIPT, again)

    assert f"client {CLIENT_ID} already exists" in output
    response = _password_grant(stack_environment, provisioned, provisioned.client_secret)
    assert response.status_code == 200, response.text
