import asyncio
import logging
from collections.abc import Awaitable, Callable, Iterator, Mapping
from contextlib import ExitStack

import pytest
import structlog
from fastapi.testclient import TestClient

from api.app import AppParts, build_app
from api.common.authentication import Caller, InvalidAccessToken
from api.common.models import DependencyCheck
from api.infrastructure.dev_data import STUB_STUDENT_ID
from tests.fake_app import FakeApp, FakeServices, fake_services


def pytest_asyncio_loop_factories(
    config: pytest.Config, item: pytest.Item
) -> Mapping[str, Callable[[], asyncio.AbstractEventLoop]]:
    # Async psycopg cannot run on Windows' default ProactorEventLoop, so no test runs on it.
    return {"selector": asyncio.SelectorEventLoop}


# configure_logging() changes global logging state; this puts it back so later tests are unaffected.
@pytest.fixture
def restore_logging() -> Iterator[None]:
    root = logging.getLogger()
    handlers, level = root.handlers[:], root.level
    yield
    root.handlers[:] = handlers
    root.setLevel(level)
    structlog.reset_defaults()


async def _no_token_is_valid(token: str) -> Caller:
    raise InvalidAccessToken


@pytest.fixture
def fake_app(restore_logging: None) -> Iterator[FakeApp]:
    """Builds the real app over fakes, through api/app.py as production does. Each client runs its
    lifespan and is closed when the test ends. The poller never runs; it has its own tests."""
    with ExitStack() as clients:

        def build(
            fakes: FakeServices | None = None,
            *,
            dependency_checks: Mapping[str, DependencyCheck] | None = None,
            verify: Callable[[str], Awaitable[Caller]] | None = None,
            enforce: bool = False,
        ) -> TestClient:
            parts = fake_services() if fakes is None else fakes
            app = build_app(
                AppParts(
                    services=parts.services,
                    caller=lambda: STUB_STUDENT_ID,
                    verify=_no_token_is_valid if verify is None else verify,
                    enforce=enforce,
                    dependency_checks={} if dependency_checks is None else dependency_checks,
                    resources=parts.resources,
                )
            )
            return clients.enter_context(TestClient(app))

        yield build
