from collections.abc import AsyncGenerator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager

import structlog
from fastapi import FastAPI
from plugin_api.file_store import FileStore

from api.common.dependencies import application_info
from api.logging_config import configure_logging, log_format

logger = structlog.stdlib.get_logger(__name__)


def lifespan(file_store: FileStore) -> Callable[[FastAPI], AbstractAsyncContextManager[None]]:
    """Startup and shutdown: configures logging, and keeps the file store open while serving."""

    @asynccontextmanager
    async def run(_app: FastAPI) -> AsyncGenerator[None]:
        configure_logging()
        logger.info(
            "server starting",
            version=application_info().version_string(),
            log_format=log_format(),
        )
        async with file_store:
            yield
        logger.info("server stopped")

    return run
