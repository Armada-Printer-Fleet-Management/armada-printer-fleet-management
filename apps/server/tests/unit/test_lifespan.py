import asyncio
import threading
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


def test_background_tasks_start_after_the_infrastructure_opens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(lifespan, "configure_logging", lambda: None)
    infrastructure = RecordingInfrastructure()
    seen: list[list[str]] = []
    started = threading.Event()

    async def task() -> None:
        seen.append(list(infrastructure.events))
        started.set()
        await asyncio.Event().wait()

    app = FastAPI(lifespan=lifespan.lifespan([infrastructure], background=[task]))
    with TestClient(app):
        assert started.wait(timeout=5)

    assert seen == [["opened"]]


def test_shutdown_cancels_the_background_tasks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(lifespan, "configure_logging", lambda: None)
    started, cancelled = threading.Event(), threading.Event()

    async def task() -> None:
        started.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            cancelled.set()
            raise

    app = FastAPI(lifespan=lifespan.lifespan([RecordingInfrastructure()], background=[task]))
    with capture_logs() as logs, TestClient(app):
        assert started.wait(timeout=5)

    assert cancelled.is_set()
    assert logs[-1]["event"] == "server stopped"
