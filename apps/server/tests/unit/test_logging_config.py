import json
import logging

import pytest
import structlog

from api.logging_config import configure_logging, log_format


def test_log_format_defaults_to_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LOG_FORMAT", raising=False)

    assert log_format() == "json"


def test_unknown_log_format_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOG_FORMAT", "xml")

    with pytest.raises(ValueError, match="LOG_FORMAT"):
        log_format()


@pytest.mark.usefixtures("restore_logging")
def test_json_lines_carry_bound_context(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("LOG_FORMAT", "json")
    configure_logging()

    with structlog.contextvars.bound_contextvars(request_id="r-1"):
        structlog.stdlib.get_logger("test").info("hello", answer=42)

    [line] = capsys.readouterr().err.splitlines()
    entry = json.loads(line)
    assert entry["event"] == "hello"
    assert entry["answer"] == 42
    assert entry["request_id"] == "r-1"
    assert entry["level"] == "info"
    assert "timestamp" in entry


@pytest.mark.usefixtures("restore_logging")
@pytest.mark.parametrize("format", ["json", "console"])
def test_tracebacks_leave_out_local_variables(
    format: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("LOG_FORMAT", format)
    configure_logging()

    # Joined at runtime, because console tracebacks print the surrounding source lines.
    def connect() -> None:
        password = "-".join(["hunter2", "secret"])
        raise ConnectionError(f"refused for {len(password)}-character password")

    try:
        connect()
    except ConnectionError:
        structlog.stdlib.get_logger("test").exception("connect failed")

    output = capsys.readouterr().err
    assert "connect failed" in output
    assert "hunter2-secret" not in output


@pytest.mark.usefixtures("restore_logging")
def test_uvicorn_records_render_through_the_same_formatter(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("LOG_FORMAT", "json")
    configure_logging()

    logging.getLogger("uvicorn.error").info("Application startup complete.")
    logging.getLogger("uvicorn.access").info("should not appear")

    [line] = capsys.readouterr().err.splitlines()
    entry = json.loads(line)
    assert entry["event"] == "Application startup complete."
    assert entry["logger"] == "uvicorn.error"
