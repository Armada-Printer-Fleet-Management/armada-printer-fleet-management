import time
from uuid import uuid4

import structlog
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = structlog.stdlib.get_logger(__name__)


# Pure ASGI rather than Starlette's BaseHTTPMiddleware, which does not reliably carry contextvars
# into the route. Added to the outer app, it also wraps the mounted ConnectRPC services.
class RequestContextMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=uuid4().hex, method=scope["method"], path=scope["path"]
        )
        status: int | None = None
        start = time.perf_counter()

        async def send_recording_status(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
            await send(message)

        try:
            await self._app(scope, receive, send_recording_status)
        except Exception:
            status = 500
            raise
        finally:
            logger.info(
                "request finished",
                status=status,
                duration_ms=round((time.perf_counter() - start) * 1000, 2),
            )
