"""The per-user settings file, and the server connection's behaviour when it holds no address."""

import re
from collections.abc import Callable
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlparse

import pytest
import yaml
from core_domain.ids import FileId, PrinterId, PrinterQueueId, PrintJobId

from armada_infrastructure.application_server.connection import (
    ApplicationServerConnection,
    ServerNotConfigured,
)
from armada_infrastructure.application_server.file import ApplicationServerFiles
from armada_infrastructure.application_server.print_job import ApplicationServerPrintJobs
from armada_infrastructure.application_server.printer import ApplicationServerPrinters
from armada_infrastructure.application_server.printer_queue import ApplicationServerPrinterQueues
from armada_runtime.environment import Environment
from armada_runtime.settings import (
    DEFAULT_AUTH_CLIENT_ID,
    DEV_AUTH_ISSUER,
    DEV_SERVER_URL,
    InvalidSettings,
    load_settings,
    settings_template,
)

DEV_COMPOSE = Path(__file__).resolve().parents[4] / "infra" / "dev" / "compose.yaml"


def test_first_launch_writes_the_template_with_the_default_url(tmp_path: Path) -> None:
    path = tmp_path / "app" / "settings.yaml"

    settings = load_settings(path, DEV_SERVER_URL)

    assert settings.server_url == DEV_SERVER_URL
    assert path.read_text(encoding="utf-8") == settings_template(DEV_SERVER_URL)


def test_packaged_default_is_empty(tmp_path: Path) -> None:
    assert load_settings(tmp_path / "settings.yaml", "").server_url == ""


@pytest.mark.parametrize("url", ['https://host/a"b', "https://host/a\\b", "https://host/#x: y"])
def test_the_template_keeps_any_url_intact(url: str) -> None:
    assert yaml.safe_load(settings_template(url))["server_url"] == url


def test_an_existing_file_is_read_and_never_overwritten(tmp_path: Path) -> None:
    path = tmp_path / "settings.yaml"
    path.write_text('server_url: "https://edited.example/api"\n', encoding="utf-8")

    settings = load_settings(path, DEV_SERVER_URL)

    assert settings.server_url == "https://edited.example/api"
    assert path.read_text(encoding="utf-8") == 'server_url: "https://edited.example/api"\n'


@pytest.mark.parametrize("content", ["server_url: [1, 2]\n", "- a list\n", "server_url: {\n"])
def test_invalid_content_raises_invalid_settings(tmp_path: Path, content: str) -> None:
    path = tmp_path / "settings.yaml"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(InvalidSettings, match=re.escape(str(path))):
        load_settings(path, DEV_SERVER_URL)


def test_first_launch_writes_the_sign_in_settings_with_their_defaults(tmp_path: Path) -> None:
    path = tmp_path / "settings.yaml"

    settings = load_settings(path, DEV_SERVER_URL, DEV_AUTH_ISSUER)

    assert (settings.auth_issuer, settings.auth_client_id) == (
        DEV_AUTH_ISSUER,
        DEFAULT_AUTH_CLIENT_ID,
    )
    written = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert written["auth_issuer"] == DEV_AUTH_ISSUER
    assert written["auth_client_id"] == DEFAULT_AUTH_CLIENT_ID


def test_a_file_from_before_sign_in_takes_the_sign_in_defaults(tmp_path: Path) -> None:
    path = tmp_path / "settings.yaml"
    path.write_text('server_url: "https://edited.example/api"\n', encoding="utf-8")

    settings = load_settings(path, DEV_SERVER_URL, DEV_AUTH_ISSUER)

    assert settings.server_url == "https://edited.example/api"
    assert (settings.auth_issuer, settings.auth_client_id) == (
        DEV_AUTH_ISSUER,
        DEFAULT_AUTH_CLIENT_ID,
    )


def test_an_empty_sign_in_setting_reads_as_empty_text(tmp_path: Path) -> None:
    path = tmp_path / "settings.yaml"
    path.write_text('server_url: ""\nauth_issuer:\n', encoding="utf-8")

    assert load_settings(path, DEV_SERVER_URL, DEV_AUTH_ISSUER).auth_issuer == ""


def test_a_sign_in_setting_that_is_not_text_raises_invalid_settings(tmp_path: Path) -> None:
    path = tmp_path / "settings.yaml"
    path.write_text("auth_client_id: [1, 2]\n", encoding="utf-8")

    with pytest.raises(InvalidSettings, match="auth_client_id"):
        load_settings(path, DEV_SERVER_URL)


def test_dev_default_matches_the_dev_compose_server_port() -> None:
    compose = yaml.safe_load(DEV_COMPOSE.read_text(encoding="utf-8"))
    published: list[str] = compose["services"]["server"]["ports"]
    host_ports = {int(mapping.split(":")[-2]) for mapping in published}

    assert urlparse(DEV_SERVER_URL).port in host_ports


def test_settings_path_needs_appdata() -> None:
    with patch.dict("os.environ", {"APPDATA": ""}), pytest.raises(RuntimeError, match="APPDATA"):
        Environment.settings_path()


def test_dev_and_packaged_use_different_settings_files(tmp_path: Path) -> None:
    with patch.dict("os.environ", {"APPDATA": str(tmp_path)}):
        dev = Environment.settings_path()
        with patch.object(Environment, "is_dev", False):
            packaged = Environment.settings_path()

    assert (dev.name, packaged.name) == ("settings.dev.yaml", "settings.yaml")
    assert dev.parent == packaged.parent


SERVER_CALLS: list[Callable[[ApplicationServerConnection], object]] = [
    lambda server: ApplicationServerPrintJobs(server).get(PrintJobId.new()),
    lambda server: ApplicationServerPrinters(server).get(PrinterId.new()),
    lambda server: ApplicationServerPrinterQueues(server).get(PrinterQueueId.new()),
    lambda server: ApplicationServerFiles(server).get(FileId.new()),
]


@pytest.mark.parametrize(
    "call", SERVER_CALLS, ids=["print_jobs", "printers", "printer_queues", "files"]
)
def test_an_unconfigured_server_fails_at_call_time_not_construction(
    tmp_path: Path, call: Callable[[ApplicationServerConnection], object]
) -> None:
    server = ApplicationServerConnection("", tmp_path / "settings.yaml")

    with pytest.raises(ServerNotConfigured, match="not configured"):
        call(server)
