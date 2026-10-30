import json
from collections.abc import Awaitable, Callable

import structlog
from core_domain.ddd import Unavailable
from starlette.types import ASGIApp, Receive, Scope, Send

from api.common.access_policy import AccessPolicy, Decision
from api.common.authentication import Caller, InvalidAccessToken, authenticated_as

logger = structlog.stdlib.get_logger(__name__)

_INVALID_TOKEN = "access token is invalid"


def _authorization(scope: Scope) -> str | None:
    for name, value in scope["headers"]:
        if name == b"authorization":
            return bytes(value).decode("latin-1")
    return None


def _bearer_token(authorization: str) -> str | None:
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


def _root_cause(error: BaseException) -> str:
    # The innermost error says why, such as an expired signature; it never holds the token.
    while error.__cause__ is not None:
        error = error.__cause__
    return f"{type(error).__name__}: {error}"


async def _reject(
    send: Send, status: int, code: str, message: str, headers: list[tuple[bytes, bytes]]
) -> None:
    # Shaped as a Connect error, so Connect clients read the code and REST clients the status.
    body = json.dumps({"code": code, "message": message}).encode()
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [(b"content-type", b"application/json"), *headers],
        }
    )
    await send({"type": "http.response.body", "body": body})


async def _reject_token(send: Send) -> None:
    await _reject(
        send,
        401,
        "unauthenticated",
        _INVALID_TOKEN,
        [(b"www-authenticate", b'Bearer error="invalid_token"')],
    )


# Pure ASGI, like RequestContextMiddleware, so it covers the mounted ConnectRPC services too.
class AuthenticationMiddleware:
    """Verifies a request's bearer token and makes its caller current for the request, then
    checks the caller against the access policy. A request without a token runs with no caller;
    one with a token that fails verification gets 401. A caller the policy refuses is logged, and
    rejected only when `enforce` is set."""

    def __init__(
        self,
        app: ASGIApp,
        verify: Callable[[str], Awaitable[Caller]],
        policy: AccessPolicy,
        enforce: bool,
    ) -> None:
        self._app = app
        self._verify = verify
        self._policy = policy
        self._enforce = enforce

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        authorization = _authorization(scope)
        caller: Caller | None = None
        if authorization is not None:
            token = _bearer_token(authorization)
            if token is None:
                logger.info("access token rejected", reason="not a bearer token")
                await _reject_token(send)
                return
            try:
                caller = await self._verify(token)
            except InvalidAccessToken as error:
                logger.info("access token rejected", reason=_root_cause(error))
                await _reject_token(send)
                return
            except Unavailable as error:
                # Only the message is reported; the cause is logged because it can name hosts.
                logger.warning("dependency unavailable", exc_info=error)
                await _reject(send, 503, "unavailable", str(error), [])
                return

        if not await self._permitted(scope, send, caller):
            return

        with authenticated_as(caller):
            await self._app(scope, receive, send)

    async def _permitted(self, scope: Scope, send: Send, caller: Caller | None) -> bool:
        """Whether the request may go on. Rejects it only when the policy is enforced."""
        decision = self._policy.decide(scope["method"], scope["path"], caller)
        if decision == Decision.ALLOW:
            return True

        logger.warning(
            "access denied" if self._enforce else "access would be denied",
            decision=decision,
            subject=caller.subject if caller else None,
            roles=sorted(caller.roles) if caller else [],
        )
        if not self._enforce:
            return True
        if decision == Decision.UNAUTHENTICATED:
            await _reject(
                send,
                401,
                "unauthenticated",
                "sign in to use this",
                [(b"www-authenticate", b"Bearer")],
            )
        else:
            await _reject(send, 403, "permission_denied", "your role does not allow this", [])
        return False
