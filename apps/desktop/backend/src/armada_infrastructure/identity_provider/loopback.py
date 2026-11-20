"""The one-shot local listener that receives the identity provider's redirect after the operator
signs in in their browser (RFC 8252 §7.3, loopback interface redirection)."""

import html
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from types import TracebackType
from typing import Self, override
from urllib.parse import parse_qs, urlsplit

CALLBACK_PATH = "/callback"
# How often the wait wakes to check whether it was cancelled.
_POLL_S = 0.25

_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{title}</title></head>
<body style="font-family: system-ui, sans-serif; margin: 4rem auto; max-width: 32rem;">
<h1>{title}</h1><p>{message}</p></body></html>
"""


class LoopbackCallback:
    """Listens on 127.0.0.1 on a port the OS picks, until the redirect arrives, the wait times
    out, or it is cancelled. Use it as a context manager so the port is always released."""

    def __init__(self) -> None:
        self._redirect: str | None = None
        self._server = HTTPServer(("127.0.0.1", 0), self._handler_class())
        self._cancelled = threading.Event()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._server.server_close()

    def redirect_uri(self) -> str:
        return f"http://127.0.0.1:{self._server.server_address[1]}{CALLBACK_PATH}"

    def cancel(self) -> None:
        self._cancelled.set()

    def receive(self, query: str) -> None:
        """Called by the request handler with the redirect's query string."""
        self._redirect = self.redirect_uri() + (f"?{query}" if query else "")

    def wait(self, timeout_s: float) -> str | None:
        """The full redirect URL, or None when the wait timed out or was cancelled."""
        deadline = time.monotonic() + timeout_s
        self._server.timeout = _POLL_S
        while self._redirect is None and not self._cancelled.is_set():
            if time.monotonic() >= deadline:
                return None
            self._server.handle_request()
        return self._redirect

    def _handler_class(self) -> type[BaseHTTPRequestHandler]:
        callback = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                url = urlsplit(self.path)
                if url.path != CALLBACK_PATH:
                    # Browsers also ask for /favicon.ico; that is not the redirect.
                    self.send_error(404)
                    return
                failed = "error" in parse_qs(url.query)
                self._page(
                    "Sign-in did not finish" if failed else "Signed in",
                    "Return to the app to see what happened and try again."
                    if failed
                    else "You can close this tab and return to the app.",
                )
                callback.receive(url.query)

            def _page(self, title: str, message: str) -> None:
                body = _PAGE.format(title=html.escape(title), message=html.escape(message))
                encoded = body.encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(encoded)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(encoded)

            @override
            def log_message(self, format: str, *args: object) -> None:
                # The default writes every request line to stderr, and this one holds the code.
                pass

        return Handler
