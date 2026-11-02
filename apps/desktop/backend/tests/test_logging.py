"""The application logger, its JSONL format, where it writes, and the log export zip."""

import json
import logging
import subprocess
import sys
import threading
import zipfile
from collections.abc import Iterator
from pathlib import Path
from types import TracebackType

import pytest

from armada_runtime.environment import Environment
from armada_runtime.log_archive import MANIFEST_NAME, LogArchive
from armada_runtime.logger import ApplicationLogger, JsonLinesFormatter
from armada_runtime.packaging import executable_name

DESKTOP_DIR = Path(__file__).resolve().parents[2]

type ExcInfo = tuple[type[BaseException], BaseException, TracebackType | None]


@pytest.fixture
def restore_logging() -> Iterator[None]:
    """install() changes process-wide state; put it back so other tests are unaffected."""
    root = logging.getLogger()
    handlers, level = root.handlers[:], root.level
    excepthook, thread_excepthook = sys.excepthook, threading.excepthook
    yield
    for handler in root.handlers:
        if handler not in handlers:
            handler.close()
    root.handlers[:] = handlers
    root.setLevel(level)
    sys.excepthook, threading.excepthook = excepthook, thread_excepthook


def format_line(formatter: JsonLinesFormatter, record: logging.LogRecord) -> dict[str, object]:
    line: dict[str, object] = json.loads(formatter.format(record))
    return line


def make_record(exc_info: ExcInfo | None = None) -> logging.LogRecord:
    return logging.getLogger("tests.logging").makeRecord(
        "tests.logging", logging.WARNING, "C:/somewhere/module.py", 42, "Queue %d%% full",
        (90,), exc_info, func="check_queue",
    )  # fmt: skip


def read_lines(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


# JSONL formatter


def test_a_line_holds_the_required_fields() -> None:
    line = format_line(JsonLinesFormatter(), make_record())

    assert line["level"] == "WARNING"
    assert line["logger"] == "tests.logging"
    assert line["message"] == "Queue 90% full"
    assert line["file"] == "module.py"
    assert line["function"] == "check_queue"
    assert line["line"] == 42
    assert str(line["timestamp"]).endswith("+00:00")


def test_an_exception_adds_its_traceback() -> None:
    try:
        raise ConnectionError("application server unreachable")
    except ConnectionError:
        kind, error, trace = sys.exc_info()
        assert kind is not None and error is not None
        line = format_line(JsonLinesFormatter(), make_record((kind, error, trace)))

    assert "Traceback" in str(line["exception"])
    assert "ConnectionError: application server unreachable" in str(line["exception"])


# Logger setup


@pytest.mark.usefixtures("restore_logging")
def test_install_writes_records_to_the_log_file(tmp_path: Path) -> None:
    log_file = tmp_path / "not-yet-created" / "app.jsonl"
    ApplicationLogger(log_file, logging.INFO).install()

    logging.getLogger("tests.logging").info("Print job approved")

    assert read_lines(log_file)[-1]["message"] == "Print job approved"


@pytest.mark.usefixtures("restore_logging")
def test_uncaught_exceptions_are_logged_as_critical_and_passed_on(tmp_path: Path) -> None:
    handed_on: list[str] = []
    sys.excepthook = lambda kind, error, trace: handed_on.append("main")
    threading.excepthook = lambda args: handed_on.append("thread")
    log_file = tmp_path / "app.jsonl"
    ApplicationLogger(log_file, logging.INFO).install()

    try:
        raise RuntimeError("main thread crash")
    except RuntimeError:
        kind, error, trace = sys.exc_info()
        assert kind is not None and error is not None
        sys.excepthook(kind, error, trace)

    def crash() -> None:
        raise RuntimeError("worker thread crash")

    worker = threading.Thread(target=crash)
    worker.start()
    worker.join()

    lines = read_lines(log_file)
    assert [line["level"] for line in lines] == ["CRITICAL", "CRITICAL"]
    assert "main thread crash" in str(lines[0]["exception"])
    assert "worker thread crash" in str(lines[1]["exception"])
    assert handed_on == ["main", "thread"]


# Log location


def test_dev_logs_go_to_the_desktop_app_folder(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Environment, "is_dev", True)

    assert Environment.log_path() == DESKTOP_DIR / "logs" / f"{executable_name()}.jsonl"


def test_packaged_logs_go_to_app_data(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(Environment, "is_dev", False)
    monkeypatch.setenv("APPDATA", str(tmp_path))

    expected = tmp_path / executable_name() / "logs" / f"{executable_name()}.jsonl"
    assert Environment.log_path() == expected


def test_dev_logs_are_gitignored(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Environment, "is_dev", True)

    ignored = subprocess.run(
        ["git", "check-ignore", "--quiet", str(Environment.log_path())],
        cwd=DESKTOP_DIR,
        check=False,
    )

    assert ignored.returncode == 0


# Export logs


def test_the_zip_holds_the_manifest_and_every_log_file(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    for name in ("app.jsonl", "app.jsonl.1", "settings.yaml"):
        (log_dir / name).write_text("{}\n", encoding="utf-8")

    destination = LogArchive(log_dir, {}).write(tmp_path / "logs.zip")

    with zipfile.ZipFile(destination) as archive:
        assert sorted(archive.namelist()) == ["app.jsonl", "app.jsonl.1", MANIFEST_NAME]


def test_the_manifest_holds_the_given_fields_and_export_time(tmp_path: Path) -> None:
    archive_path = LogArchive(tmp_path, {"version": "1.2.3", "os": "Windows-11"}).write(
        tmp_path / "logs.zip"
    )

    with zipfile.ZipFile(archive_path) as archive:
        manifest = json.loads(archive.read(MANIFEST_NAME))

    assert manifest["version"] == "1.2.3"
    assert manifest["os"] == "Windows-11"
    assert "exported_at" in manifest
