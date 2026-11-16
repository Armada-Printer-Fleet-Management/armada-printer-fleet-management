"""OidcSessions with Authlib's client and the discovery request mocked. The loopback listener is
real; a stand-in browser follows the redirect back to it."""

import base64
import json
import threading
from collections.abc import Callable, Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import urlopen

import pytest
import requests
from authlib.common.errors import AuthlibBaseError

from armada_domains.auth.errors import SignInFailed, SignInRequired
from armada_infrastructure.identity_provider.oidc_sessions import (
    OidcSessions,
    SignInNotConfigured,
)

MODULE = "armada_infrastructure.identity_provider.oidc_sessions"
ISSUER = "https://idp.example/realms/armada"
CLIENT_ID = "armada-desktop"
SETTINGS = Path("settings.yaml")
# An unsigned ID token: the adapter reads its claims without checking a signature.
ID_TOKEN = (
    ".".join(
        base64.urlsafe_b64encode(json.dumps(part).encode()).decode().rstrip("=")
        for part in ({"alg": "none"}, {"sid": "provider-session-1"})
    )
    + "."
)
METADATA = {
    "authorization_endpoint": f"{ISSUER}/auth",
    "token_endpoint": f"{ISSUER}/token",
    "userinfo_endpoint": f"{ISSUER}/userinfo",
    "end_session_endpoint": f"{ISSUER}/logout",
}


@pytest.fixture
def client() -> Iterator[MagicMock]:
    """The OAuth2Session the adapter builds, and the provider's discovery document."""
    with (
        patch(f"{MODULE}.OAuth2Session") as session_type,
        patch(f"{MODULE}.requests.get") as get,
    ):
        get.return_value.json.return_value = METADATA
        client = session_type.return_value

        def authorize(url: str, code_verifier: str) -> tuple[str, str]:
            redirect = session_type.call_args.kwargs["redirect_uri"]
            return f"{url}?{urlencode({'redirect_uri': redirect})}", "state-1"

        client.create_authorization_url.side_effect = authorize
        client.get.return_value.json.return_value = {
            "email": "operator@example.edu",
            "given_name": "An",
            "family_name": "Operator",
        }
        client.fetch_token.return_value = {"id_token": ID_TOKEN}
        client.token = {"access_token": "access-1", "refresh_token": "refresh-1"}
        yield client


def browser(query: str) -> Callable[[str], None]:
    """Stands in for the operator's browser: comes back to the loopback with this query."""

    def open_browser(url: str) -> None:
        redirect = parse_qs(urlsplit(url).query)["redirect_uri"][0]
        threading.Thread(
            target=lambda: urlopen(f"{redirect}?{query}", timeout=5).read(), daemon=True
        ).start()

    return open_browser


def sessions(open_browser: Callable[[str], None], timeout_s: float = 5.0) -> OidcSessions:
    return OidcSessions(ISSUER, CLIENT_ID, SETTINGS, open_browser, timeout_s)


@pytest.fixture
def signed_in(client: MagicMock) -> OidcSessions:
    signed = sessions(browser("code=code-1&state=state-1"))
    signed.sign_in()
    return signed


# Sign-in refusals


def test_sign_in_without_an_issuer_says_which_file_to_set() -> None:
    unconfigured = OidcSessions("", CLIENT_ID, SETTINGS)

    with pytest.raises(SignInNotConfigured, match="settings.yaml"):
        unconfigured.sign_in()


def test_sign_in_cancelled_at_the_provider_says_so(client: MagicMock) -> None:
    with pytest.raises(SignInFailed, match="cancelled"):
        sessions(browser("error=access_denied&state=state-1")).sign_in()


def test_sign_in_refused_for_another_reason_gives_the_providers_description(
    client: MagicMock,
) -> None:
    query = "error=invalid_scope&error_description=Unknown+scope&state=state-1"

    with pytest.raises(SignInFailed, match="Unknown scope"):
        sessions(browser(query)).sign_in()


def test_sign_in_with_no_redirect_times_out(client: MagicMock) -> None:
    with pytest.raises(SignInFailed, match="timed out"):
        sessions(lambda url: None, timeout_s=0.3).sign_in()


# Token renewal and the ended flag


def test_a_current_token_is_returned_after_checking_it(
    client: MagicMock, signed_in: OidcSessions
) -> None:
    assert signed_in.access_token() == "access-1"
    client.ensure_active_token.assert_called_once()


def test_a_refused_renewal_ends_the_session_and_requires_sign_in_until_then(
    client: MagicMock, signed_in: OidcSessions
) -> None:
    client.ensure_active_token.side_effect = AuthlibBaseError("invalid_grant")

    for _ in range(2):
        with pytest.raises(SignInRequired, match="session has ended"):
            signed_in.access_token()
    assert signed_in.session() is None


def test_an_unreachable_provider_sends_no_token_but_keeps_the_session(
    client: MagicMock, signed_in: OidcSessions
) -> None:
    client.ensure_active_token.side_effect = requests.ConnectionError("down")

    assert signed_in.access_token() is None
    session = signed_in.session()
    assert session is not None and session.email == "operator@example.edu"


# Sign-out


def test_sign_out_after_an_ended_session_clears_the_requirement(
    client: MagicMock, signed_in: OidcSessions
) -> None:
    client.ensure_active_token.side_effect = AuthlibBaseError("invalid_grant")
    with pytest.raises(SignInRequired):
        signed_in.access_token()

    signed_in.sign_out()

    assert signed_in.access_token() is None
    assert signed_in.session() is None


def test_sign_out_ends_the_providers_session(client: MagicMock, signed_in: OidcSessions) -> None:
    signed_in.sign_out()

    assert signed_in.session() is None
    client.post.assert_called_once()
    url, data = client.post.call_args.args[0], client.post.call_args.kwargs["data"]
    assert url == METADATA["end_session_endpoint"]
    assert data == {"client_id": CLIENT_ID, "refresh_token": "refresh-1"}
    client.close.assert_called_once()


def test_sign_out_still_signs_out_here_when_the_provider_is_unreachable(
    client: MagicMock, signed_in: OidcSessions
) -> None:
    client.post.side_effect = requests.ConnectionError("down")

    signed_in.sign_out()

    assert signed_in.session() is None
    assert signed_in.access_token() is None
