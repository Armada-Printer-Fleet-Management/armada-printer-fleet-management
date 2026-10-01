import pytest
from fastapi.testclient import TestClient
from structlog.testing import capture_logs

from api import lifespan
from api.common.dependencies import application_info
from api.main import app


# configure_logging() is replaced so it cannot reconfigure structlog over capture_logs().
def test_lifespan_configures_logging_and_logs_start_and_stop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[None] = []
    monkeypatch.setattr(lifespan, "configure_logging", lambda: calls.append(None))

    with capture_logs() as logs, TestClient(app):
        pass

    assert calls == [None]
    events = [entry["event"] for entry in logs]
    assert events == ["server starting", "server stopped"]
    assert logs[0]["version"] == application_info().version_string()
