import logging
from collections.abc import Iterator

import pytest
import structlog


# configure_logging() changes global logging state; this puts it back so later tests are unaffected.
@pytest.fixture
def restore_logging() -> Iterator[None]:
    root = logging.getLogger()
    handlers, level = root.handlers[:], root.level
    yield
    root.handlers[:] = handlers
    root.setLevel(level)
    structlog.reset_defaults()
