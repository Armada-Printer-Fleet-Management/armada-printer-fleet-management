"""The loopback listener, over a real socket on 127.0.0.1."""

import threading
from urllib.error import URLError
from urllib.request import urlopen

import pytest

from armada_infrastructure.identity_provider.loopback import LoopbackCallback


def visit(url: str, pages: list[str]) -> threading.Thread:
    """Stands in for the browser following the redirect, keeping the page it was shown."""

    def run() -> None:
        with urlopen(url, timeout=5) as response:
            pages.append(response.read().decode())

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread


def test_wait_returns_the_full_redirect_and_shows_signed_in() -> None:
    pages: list[str] = []
    with LoopbackCallback() as callback:
        redirect = f"{callback.redirect_uri()}?code=code-1&state=state-1"
        browser = visit(redirect, pages)

        assert callback.wait(5) == redirect
    browser.join(5)

    assert "Signed in" in pages[0]


def test_an_error_redirect_shows_the_failure_page_and_the_port_is_freed() -> None:
    pages: list[str] = []
    with LoopbackCallback() as callback:
        redirect_uri = callback.redirect_uri()
        browser = visit(f"{redirect_uri}?error=access_denied&state=state-1", pages)
        callback.wait(5)
    browser.join(5)

    assert "Sign-in did not finish" in pages[0]
    with pytest.raises(URLError):
        urlopen(redirect_uri, timeout=2)
