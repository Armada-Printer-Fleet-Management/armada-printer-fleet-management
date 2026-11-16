import base64
import binascii
import json
import threading
import webbrowser
from collections.abc import Callable
from functools import cached_property
from pathlib import Path
from typing import cast
from urllib.parse import parse_qs, urlsplit

import requests
from authlib.common.errors import AuthlibBaseError
from authlib.common.security import generate_token
from authlib.integrations.requests_client import OAuth2Session
from core_domain.auth import Session
from core_domain.ddd import EntityNotFound, RuleViolation, Unavailable
from core_domain.ids import SessionId

from armada_domains.auth.errors import SignInFailed, SignInRequired
from armada_domains.auth.repository import SessionRepository
from armada_infrastructure.identity_provider.loopback import LoopbackCallback

_PROVIDER = "sign-in provider"
_HTTP_TIMEOUT_S = 10.0
# Must match the client's pkce.code.challenge.method in infra/deploy/armada-realm.json.
_PKCE_METHOD = "S256"
# Long enough to type a password and pass any second factor.
SIGN_IN_TIMEOUT_S = 300.0


class SignInNotConfigured(SignInFailed):
    def __init__(self, settings_path: Path) -> None:
        super().__init__(
            f"Sign-in is not configured. Set auth_issuer in {settings_path} and restart the app."
        )


class OidcSessions(SessionRepository):
    """Signs the operator in at an OpenID Connect provider with the authorization code flow and
    PKCE, through their own browser and a loopback redirect, then keeps the tokens in memory and
    renews them. Only access_token() hands a token out, and only to this app's own transport."""

    def __init__(
        self,
        issuer: str,
        client_id: str,
        settings_path: Path,
        open_browser: Callable[[str], object] = webbrowser.open,
        sign_in_timeout_s: float = SIGN_IN_TIMEOUT_S,
    ) -> None:
        self._issuer = issuer.rstrip("/")
        self._client_id = client_id
        self._settings_path = settings_path
        self._open_browser = open_browser
        self._sign_in_timeout_s = sign_in_timeout_s
        # Guards the signed-in state, which IPC calls and server calls reach from many threads.
        self._lock = threading.Lock()
        self._client: OAuth2Session | None = None
        self._session: Session | None = None
        # Set when the provider refuses a renewal, until the operator signs in or out again.
        self._ended = False
        self._pending: LoopbackCallback | None = None

    def sign_in(self) -> Session:
        if not self._issuer:
            raise SignInNotConfigured(self._settings_path)
        metadata = self._metadata
        with LoopbackCallback() as callback:
            self._replace_pending(callback)
            try:
                client = OAuth2Session(
                    self._client_id,
                    scope="openid profile email",
                    redirect_uri=callback.redirect_uri(),
                    code_challenge_method=_PKCE_METHOD,
                    token_endpoint=metadata["token_endpoint"],
                    default_timeout=_HTTP_TIMEOUT_S,
                )
                verifier = generate_token(48)
                url, state = client.create_authorization_url(
                    metadata["authorization_endpoint"], code_verifier=verifier
                )
                self._open_browser(url)
                redirect = callback.wait(self._sign_in_timeout_s)
            finally:
                self._clear_pending(callback)

        if redirect is None:
            raise SignInFailed("Sign-in timed out or was restarted. Select Sign in to try again.")
        _raise_for_refusal(redirect)
        session = self._finish(client, metadata, redirect, verifier, state)
        with self._lock:
            self._client, self._session, self._ended = client, session, False
        return session

    def sign_out(self) -> None:
        with self._lock:
            client, self._client, self._session = self._client, None, None
            self._ended = False
        if client is None:
            return
        refresh_token = (client.token or {}).get("refresh_token")
        end_session = self._metadata.get("end_session_endpoint")
        if isinstance(refresh_token, str) and end_session:
            # Ends the provider's session too, so the next sign-in on this machine asks again
            # instead of silently reusing the browser's sign-in.
            try:
                client.post(
                    end_session,
                    data={"client_id": self._client_id, "refresh_token": refresh_token},
                    timeout=_HTTP_TIMEOUT_S,
                )
            except requests.RequestException:
                pass
        client.close()

    def session(self) -> Session | None:
        with self._lock:
            return self._session

    def get(self, entity_id: SessionId) -> Session:
        session = self.session()
        if session is None or session.id != entity_id:
            raise EntityNotFound(entity_id)
        return session

    def access_token(self) -> str | None:
        """A current access token, renewed first when it is about to expire, or None when
        nobody is signed in. A renewal the provider refuses ends the session, and from then until
        the next sign-in or sign-out this raises SignInRequired, so no call goes out without it."""
        with self._lock:
            if self._ended:
                raise _session_ended()
            client = self._client
            if client is None:
                return None
            try:
                client.ensure_active_token(client.token)
            except AuthlibBaseError as error:
                self._client, self._session, self._ended = None, None, True
                client.close()
                raise _session_ended() from error
            except requests.RequestException:
                # The provider is unreachable; the server decides what an unsigned call gets.
                return None
            token = (client.token or {}).get("access_token")
            return token if isinstance(token, str) else None

    @cached_property
    def _metadata(self) -> dict[str, str]:
        url = f"{self._issuer}/.well-known/openid-configuration"
        try:
            response = requests.get(url, timeout=_HTTP_TIMEOUT_S)
            response.raise_for_status()
            body = cast(dict[str, object], response.json())
        except (requests.RequestException, ValueError) as error:
            raise Unavailable(_PROVIDER) from error
        return {key: value for key, value in body.items() if isinstance(value, str)}

    def _finish(
        self,
        client: OAuth2Session,
        metadata: dict[str, str],
        redirect: str,
        verifier: str,
        state: str,
    ) -> Session:
        try:
            token = client.fetch_token(
                metadata["token_endpoint"],
                authorization_response=redirect,
                code_verifier=verifier,
                state=state,
            )
            response = client.get(metadata["userinfo_endpoint"], timeout=_HTTP_TIMEOUT_S)
            response.raise_for_status()
            claims = cast(dict[str, object], response.json())
        except AuthlibBaseError as error:
            client.close()
            raise SignInFailed(
                "The sign-in provider did not accept the sign-in. Select Sign in to try again."
            ) from error
        except (requests.RequestException, ValueError) as error:
            client.close()
            raise Unavailable(_PROVIDER) from error

        try:
            return Session.from_provider(
                self._issuer,
                _claim(_id_token_claims(token), "sid"),
                _claim(claims, "email"),
                _claim(claims, "given_name"),
                _claim(claims, "family_name"),
            )
        except RuleViolation as error:
            client.close()
            raise SignInFailed(
                "The sign-in provider did not report a complete sign-in. Select Sign in to try "
                "again."
            ) from error

    def _replace_pending(self, callback: LoopbackCallback) -> None:
        # Selecting Sign in again restarts the flow, so a closed browser tab is never a dead end.
        with self._lock:
            if self._pending is not None:
                self._pending.cancel()
            self._pending = callback

    def _clear_pending(self, callback: LoopbackCallback) -> None:
        with self._lock:
            if self._pending is callback:
                self._pending = None


def _session_ended() -> SignInRequired:
    return SignInRequired("Your session has ended.")


def _raise_for_refusal(redirect: str) -> None:
    params = parse_qs(urlsplit(redirect).query)
    error = params.get("error", [""])[0]
    if error == "access_denied":
        raise SignInFailed("Sign-in was cancelled. Select Sign in to try again.")
    if error:
        description = params.get("error_description", [error])[0]
        raise SignInFailed(f"The sign-in provider refused the sign-in: {description}")


def _id_token_claims(token: dict[str, object]) -> dict[str, object]:
    """The ID token's claims, unverified: it came straight from the provider's token endpoint
    over TLS, which OpenID Connect Core 3.1.3.7 accepts in place of checking its signature."""
    id_token = token.get("id_token")
    if not isinstance(id_token, str) or id_token.count(".") != 2:
        return {}
    payload = id_token.split(".")[1]
    try:
        claims: object = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    except (binascii.Error, ValueError):
        return {}
    return cast(dict[str, object], claims) if isinstance(claims, dict) else {}


def _claim(claims: dict[str, object], name: str) -> str:
    value = claims.get(name)
    return value if isinstance(value, str) else ""
