from types import TracebackType
from typing import Self

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from structlog.testing import capture_logs

from api import lifespan
from api.common.dependencies import application_info


class RecordingInfrastructure:
    """Infrastructure that only records being opened and closed."""

    def __init__(self) -> None:
        self.events: list[str] = []

    async def __aenter__(self) -> Self:
        self.events.append("opened")
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.events.append("closed")


# configure_logging() is replaced so it cannot reconfigure structlog over capture_logs().
def test_lifespan_configures_logging_and_logs_start_and_stop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[None] = []
    monkeypatch.setattr(lifespan, "configure_logging", lambda: calls.append(None))

    app = FastAPI(lifespan=lifespan.lifespan([RecordingInfrastructure()]))

    with capture_logs() as logs, TestClient(app):
        pass

    assert calls == [None]
    events = [entry["event"] for entry in logs]
    assert events == ["server starting", "server stopped"]
    assert logs[0]["version"] == application_info().version_string()


def test_lifespan_keeps_the_infrastructure_open_while_serving(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(lifespan, "configure_logging", lambda: None)
    infrastructure = RecordingInfrastructure()

    with TestClient(FastAPI(lifespan=lifespan.lifespan([infrastructure]))):
        assert infrastructure.events == ["opened"]

    assert infrastructure.events == ["opened", "closed"]
