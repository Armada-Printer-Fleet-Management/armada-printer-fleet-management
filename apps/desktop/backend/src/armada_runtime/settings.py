"""The per-user desktop settings file: generated on first launch, then only read."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import yaml

# The dev compose server, as published on this machine by infra/dev/compose.yaml.
DEV_SERVER_URL = "http://localhost:8000/api"
# Keycloak through the dev web container's proxy. It must equal the dev server's AUTH_ISSUER,
# because Keycloak names the issuer after the address it was reached on.
DEV_AUTH_ISSUER = "http://localhost:5174/auth/realms/armada"
# The desktop's client in infra/deploy/armada-realm.json.
DEFAULT_AUTH_CLIENT_ID = "armada-desktop"


class InvalidSettings(Exception):
    def __init__(self, path: Path, problem: str) -> None:
        super().__init__(f"The settings file {path} is invalid: {problem}")


@dataclass(frozen=True)
class DesktopSettings:
    server_url: str
    auth_issuer: str
    auth_client_id: str


def settings_template(
    server_url: str, auth_issuer: str = "", auth_client_id: str = DEFAULT_AUTH_CLIENT_ID
) -> str:
    # A JSON string is a valid YAML double-quoted scalar, so any URL is escaped correctly.
    return f"""\
# Desktop connection settings. Created on first launch and never overwritten afterwards, so your
# edits are kept. Changes take effect the next time the app starts.

# The application server's API address, for example https://armada.example.edu/api.
# Leave it empty and every call that needs the server fails with "server not configured".
server_url: {json.dumps(server_url)}

# The sign-in provider's OpenID Connect issuer, for example
# https://armada.example.edu/auth/realms/armada. Leave it empty and sign-in is unavailable.
auth_issuer: {json.dumps(auth_issuer)}

# This app's client ID at the sign-in provider.
auth_client_id: {json.dumps(auth_client_id)}
"""


def load_settings(
    path: Path,
    default_server_url: str,
    default_auth_issuer: str = "",
    default_auth_client_id: str = DEFAULT_AUTH_CLIENT_ID,
) -> DesktopSettings:
    """Reads the settings file, first generating it if it does not exist. A sign-in setting
    missing from an older file takes its default, so a file written before sign-in still works."""
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        # "x" refuses to replace a file, in case one appeared since the check above.
        with path.open("x", encoding="utf-8") as file:
            file.write(
                settings_template(default_server_url, default_auth_issuer, default_auth_client_id)
            )

    try:
        content: object = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise InvalidSettings(path, f"it is not valid YAML ({error})") from error
    if not isinstance(content, dict):
        raise InvalidSettings(path, "it must be a mapping of setting names to values")
    values = cast(dict[str, object], content)

    return DesktopSettings(
        server_url=_text(path, values, "server_url", ""),
        auth_issuer=_text(path, values, "auth_issuer", default_auth_issuer),
        auth_client_id=_text(path, values, "auth_client_id", default_auth_client_id),
    )


def _text(path: Path, values: dict[str, object], name: str, missing: str) -> str:
    value = values.get(name, missing)
    if value is None:
        value = ""
    if not isinstance(value, str):
        raise InvalidSettings(path, f"{name} must be text")
    return value.strip()
