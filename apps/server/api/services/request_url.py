from connectrpc.code import Code
from connectrpc.errors import ConnectError
from connectrpc.request import RequestContext


def absolute_url[Req, Res](ctx: RequestContext[Req, Res], path: str) -> str:
    """The path on the origin the caller reached the server through. Proxies in front of the
    server keep the caller's Host, and report an HTTPS origin in X-Forwarded-Proto."""
    host = ctx.request_headers.get("host")
    if not host:
        raise ConnectError(Code.INVALID_ARGUMENT, "the Host header is required")
    scheme = ctx.request_headers.get("x-forwarded-proto", "http")
    return f"{scheme}://{host}{path}"
