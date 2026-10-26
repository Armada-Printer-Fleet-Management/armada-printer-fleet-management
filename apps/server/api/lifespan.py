import asyncio
from collections.abc import AsyncGenerator, Callable, Coroutine, Iterable
from contextlib import AbstractAsyncContextManager, AsyncExitStack, asynccontextmanager

import structlog
from fastapi import FastAPI

from api.common.dependencies import application_info
from api.logging_config import configure_logging, log_format

logger = structlog.stdlib.get_logger(__name__)


def lifespan(
    infrastructure: Iterable[AbstractAsyncContextManager[object]],
    background: Iterable[Callable[[], Coroutine[object, object, None]]] = (),
) -> Callable[[FastAPI], AbstractAsyncContextManager[None]]:
    """Startup and shutdown: configures logging, keeps the infrastructure open while serving, and
    runs the background tasks until shutdown cancels them."""

    @asynccontextmanager
    async def run(_app: FastAPI) -> AsyncGenerator[None]:
        configure_logging()
        logger.info(
            "server starting",
            version=application_info().version_string(),
            log_format=log_format(),
        )
        async with AsyncExitStack() as stack:
            for each in infrastructure:
                await stack.enter_async_context(each)
            tasks = [asyncio.create_task(task()) for task in background]
            try:
                yield
            finally:
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("server stopped")

    return run
