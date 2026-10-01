from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from api.common.dependencies import application_info
from api.logging_config import configure_logging, log_format

logger = structlog.stdlib.get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    configure_logging()
    logger.info(
        "server starting",
        version=application_info().version_string(),
        log_format=log_format(),
    )
    yield
    logger.info("server stopped")
