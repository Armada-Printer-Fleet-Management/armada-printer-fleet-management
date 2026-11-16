"""The BearerToken interceptor, alone and inside a real Connect client."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from core_domain.ids import PrinterId

from armada_domains.auth.errors import SignInRequired
from armada_infrastructure.application_server.bearer_token import BearerToken
from armada_infrastructure.application_server.connection import ApplicationServerConnection
from armada_infrastructure.application_server.printer import ApplicationServerPrinters

# Nothing listens here, so a call that got as far as the network would fail as unavailable.
UNREACHABLE = "http://127.0.0.1:9/api"


def request_context() -> MagicMock:
    ctx = MagicMock()
    ctx.request_headers = {}
    return ctx


def test_a_token_is_sent_as_a_bearer_header() -> None:
    ctx = request_context()

    BearerToken(lambda: "access-1").on_start_sync(ctx)

    assert ctx.request_headers == {"authorization": "Bearer access-1"}


@pytest.mark.parametrize("token", [None, ""])
def test_no_token_sends_no_header(token: str | None) -> None:
    ctx = request_context()

    BearerToken(lambda: token).on_start_sync(ctx)

    assert ctx.request_headers == {}


def test_a_token_source_requiring_sign_in_stops_the_call_before_it_is_sent() -> None:
    def ended() -> str | None:
        raise SignInRequired("Your session has ended.")

    printers = ApplicationServerPrinters(
        ApplicationServerConnection(UNREACHABLE, Path("settings.yaml"), access_token=ended)
    )

    with pytest.raises(SignInRequired):
        printers.get(PrinterId.new())
