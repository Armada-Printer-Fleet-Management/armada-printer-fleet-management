import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

import httpx2
from connectrpc.request import RequestContext

from e2e.settings import E2eRole, E2eSettings

# Keycloak's access tokens last five minutes; one this close to expiry is replaced before use.
_EXPIRY_MARGIN_S = 30.0


class SignInFailed(Exception):
    pass


@dataclass(frozen=True)
class _Token:
    value: str
    expires_at: float


class KeycloakTokens:
    """Signs each test user in with a real password grant and keeps their token until it is
    about to expire, so every request carries a token the identity provider actually issued."""

    def __init__(
        self,
        settings: E2eSettings,
        http: httpx2.Client,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._settings = settings
        self._http = http
        self._clock = clock
        self._tokens: dict[E2eRole, _Token] = {}

    def token(self, role: E2eRole) -> str:
        cached = self._tokens.get(role)
        if cached is None or cached.expires_at - _EXPIRY_MARGIN_S <= self._clock():
            cached = self._tokens[role] = self._sign_in(role)
        return cached.value

    def _sign_in(self, role: E2eRole) -> _Token:
        username, password = self._settings.credentials(role)
        requested_at = self._clock()
        try:
            response = self._http.post(
                self._settings.token_url(),
                data={
                    "grant_type": "password",
                    "client_id": self._settings.auth_client_id,
                    "client_secret": self._settings.auth_client_secret.get_secret_value(),
                    "username": username,
                    "password": password,
                    "scope": "openid",
                },
            )
        except httpx2.HTTPError as error:
            raise SignInFailed(
                f"Keycloak is unreachable at {self._settings.token_url()}"
            ) from error
        if response.status_code != 200:
            raise SignInFailed(_refusal(role, username, response))
        body = cast(dict[str, object], response.json())
        token, expires_in = body.get("access_token"), body.get("expires_in")
        if not isinstance(token, str) or not isinstance(expires_in, int):
            raise SignInFailed(f"Keycloak's token response for {role} has no access token")
        return _Token(token, requested_at + expires_in)


def _refusal(role: E2eRole, username: str, response: httpx2.Response) -> str:
    try:
        body = cast(dict[str, object], response.json())
    except ValueError:
        body = {}
    error, description = body.get("error"), body.get("error_description")
    because = f" (Keycloak: {description})" if isinstance(description, str) else ""
    if error in ("unauthorized_client", "invalid_client"):
        return (
            "Keycloak refused the e2e client: check E2E_AUTH_CLIENT_ID and E2E_AUTH_CLIENT_SECRET, "
            f"and that the client is confidential with direct access grants enabled{because}"
        )
    if error == "invalid_grant":
        # Keycloak also answers invalid_grant for a user with a pending required action, such as
        # a profile missing the first name, last name or email its user profile requires.
        return (
            f"The {role} test user {username!r} could not sign in{because}: check its password, "
            "and that its profile is complete with no required user actions"
        )
    return f"Keycloak answered {response.status_code} when signing in the {role} test user{because}"


class BearerToken:
    """A Connect interceptor that signs every call in as one test role."""

    def __init__(self, tokens: KeycloakTokens, role: E2eRole) -> None:
        self._tokens = tokens
        self._role = role

    def on_start_sync(self, ctx: RequestContext[object, object]) -> None:
        ctx.request_headers["authorization"] = f"Bearer {self._tokens.token(self._role)}"

    def on_end_sync(
        self, token: None, ctx: RequestContext[object, object], error: Exception | None
    ) -> None:
        return None
