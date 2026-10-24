"""The per-user desktop settings file: generated on first launch, then only read."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import yaml

# The dev compose server, as published on this machine by infra/dev/compose.yaml.
DEV_SERVER_URL = "http://localhost:8000/api"


class InvalidSettings(Exception):
    def __init__(self, path: Path, problem: str) -> None:
        super().__init__(f"The settings file {path} is invalid: {problem}")


@dataclass(frozen=True)
class DesktopSettings:
    server_url: str


def settings_template(server_url: str) -> str:
    # A JSON string is a valid YAML double-quoted scalar, so any URL is escaped correctly.
    return f"""\
# Desktop connection settings. Created on first launch and never overwritten afterwards, so your
# edits are kept. Changes take effect the next time the app starts.

# The application server's API address, for example https://armada.example.edu/api.
# Leave it empty and every call that needs the server fails with "server not configured".
server_url: {json.dumps(server_url)}
"""


def load_settings(path: Path, default_server_url: str) -> DesktopSettings:
    """Reads the settings file, first generating it if it does not exist."""
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        # "x" refuses to replace a file, in case one appeared since the check above.
        with path.open("x", encoding="utf-8") as file:
            file.write(settings_template(default_server_url))

    try:
        content: object = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise InvalidSettings(path, f"it is not valid YAML ({error})") from error
    if not isinstance(content, dict):
        raise InvalidSettings(path, "it must be a mapping of setting names to values")

    server_url = cast(dict[str, object], content).get("server_url") or ""
    if not isinstance(server_url, str):
        raise InvalidSettings(path, "server_url must be text")
    return DesktopSettings(server_url=server_url.strip())
