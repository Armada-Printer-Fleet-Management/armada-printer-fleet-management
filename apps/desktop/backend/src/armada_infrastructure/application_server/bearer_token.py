from collections.abc import Callable

from connectrpc.request import RequestContext

# Returns the current access token, or None when nobody is signed in.
type AccessToken = Callable[[], str | None]


def no_access_token() -> str | None:
    return None


class BearerToken:
    """Adds the signed-in operator's access token to every call, as a connectrpc metadata
    interceptor. The token is asked for per call, so a renewed one is always the one sent. The
    token source may raise SignInRequired instead, which stops the call before it is sent."""

    def __init__(self, access_token: AccessToken) -> None:
        self._access_token = access_token

    def on_start_sync(self, ctx: RequestContext[object, object], /) -> None:
        token = self._access_token()
        if token:
            ctx.request_headers["authorization"] = f"Bearer {token}"

    def on_end_sync(
        self, token: None, ctx: RequestContext[object, object], error: Exception | None, /
    ) -> None:
        return
