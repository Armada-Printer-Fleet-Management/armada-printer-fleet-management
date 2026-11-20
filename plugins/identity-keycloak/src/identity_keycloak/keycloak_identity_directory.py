import time
from collections.abc import Callable, Mapping
from contextlib import suppress
from http import HTTPStatus
from types import TracebackType
from typing import Self, cast
from urllib.parse import quote, urlencode

import httpx2
from plugin_api.identity_directory import AccountExistsError, IdentityDirectoryError, NewAccount

# Renew a little before the token's own expiry, so a request never carries one that lapses in
# flight.
_TOKEN_RENEWAL_MARGIN_SECONDS = 30.0
_KEYCLOAK_USERS_URL = "/users"
type _Json = Mapping[str, object] | list[object]


def _segment(value: str) -> str:
    return quote(value, safe="")


def _member(value: object, name: str) -> object:
    """A JSON object's member, or None when value is not an object."""
    if isinstance(value, dict):
        return cast(dict[str, object], value).get(name)
    return None


class KeycloakIdentityDirectory:
    def __init__(
        self,
        *,
        base_url: str,
        realm: str,
        client_id: str,
        client_secret: str,
        transport: httpx2.AsyncBaseTransport | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        base = base_url.rstrip("/")
        self._token_url = f"{base}/realms/{_segment(realm)}/protocol/openid-connect/token"
        self._admin_url = f"{base}/admin/realms/{_segment(realm)}"
        self._client_id = client_id
        self._client_secret = client_secret
        self._transport = transport
        self._clock = clock
        self._client: httpx2.AsyncClient | None = None
        self._token: str | None = None
        self._token_expires_at = 0.0

    def _http(self) -> httpx2.AsyncClient:
        if self._client is None:
            raise IdentityDirectoryError("Keycloak client is not initialized")
        return self._client

    async def __aenter__(self) -> Self:
        self._client = httpx2.AsyncClient(
            transport=self._transport, timeout=httpx2.Timeout(5.0, connect=3.0)
        )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        client, self._client = self._client, None
        self._token = None
        if client is not None:
            await client.aclose()

    async def _fetch_token(self) -> str:
        try:
            response = await self._http().post(
                self._token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                },
            )
            response.raise_for_status()
            body = cast(object, response.json())
        except (httpx2.HTTPError, ValueError) as error:
            raise IdentityDirectoryError("Failed to get a Keycloak admin token") from error
        if not isinstance(body, dict):
            raise IdentityDirectoryError("Keycloak returned a malformed token response")
        token = cast(dict[str, object], body).get("access_token")
        expires_in = cast(dict[str, object], body).get("expires_in")
        if not isinstance(token, str) or not isinstance(expires_in, int):
            raise IdentityDirectoryError("Keycloak returned a malformed token response")
        self._token = token
        self._token_expires_at = self._clock() + expires_in - _TOKEN_RENEWAL_MARGIN_SECONDS
        return token

    async def _access_token(self) -> str:
        if self._token is not None and self._clock() < self._token_expires_at:
            return self._token
        return await self._fetch_token()

    async def _request(self, method: str, path: str, json: _Json | None = None) -> httpx2.Response:
        """An admin API request. A 401 means the cached token was revoked or expired early, so it
        is renewed and the request tried once more."""
        url = f"{self._admin_url}{path}"
        try:
            token = await self._access_token()
            response = await self._http().request(
                method, url, json=json, headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == HTTPStatus.UNAUTHORIZED:
                token = await self._fetch_token()
                response = await self._http().request(
                    method, url, json=json, headers={"Authorization": f"Bearer {token}"}
                )
        except httpx2.HTTPError as error:
            raise IdentityDirectoryError(f"Keycloak {method} request failed") from error
        return response

    async def create_account(self, account: NewAccount) -> str:
        response = await self._request(
            "POST",
            _KEYCLOAK_USERS_URL,
            {
                "username": account.email,
                "email": account.email,
                "firstName": account.first_name,
                "lastName": account.last_name,
                "enabled": True,
            },
        )
        if response.status_code == HTTPStatus.CONFLICT:
            raise AccountExistsError("An account with this email already exists")
        if response.status_code != HTTPStatus.CREATED:
            raise IdentityDirectoryError(f"Keycloak refused the account ({response.status_code})")
        subject = response.headers.get("Location", "").rstrip("/").rpartition("/")[2]
        if not subject:
            subject = await self._subject_of(account.email)

        try:
            await self._assign_realm_role(subject, account.role)
        except Exception:
            # The port promises a failed create leaves nothing behind. A removal that fails too
            # must not hide why the create failed.
            with suppress(IdentityDirectoryError):
                await self.delete_account(subject)
            raise
        return subject

    async def _subject_of(self, username: str) -> str:
        """The subject of the account with exactly this username, for a create whose response did
        not say where the account is."""
        response = await self._request(
            "GET", f"{_KEYCLOAK_USERS_URL}?{urlencode({'username': username, 'exact': 'true'})}"
        )
        if response.status_code != HTTPStatus.OK:
            raise IdentityDirectoryError(
                f"Keycloak refused the user lookup ({response.status_code})"
            )
        try:
            users = cast(object, response.json())
        except ValueError as error:
            raise IdentityDirectoryError("Keycloak returned a malformed user list") from error
        if isinstance(users, list):
            for user in cast(list[object], users):
                subject = _member(user, "id")
                if isinstance(subject, str) and subject:
                    return subject
        raise IdentityDirectoryError("Keycloak created the account but cannot find it")

    async def _assign_realm_role(self, subject: str, role: str) -> None:
        response = await self._request("GET", f"/roles/{_segment(role)}")
        if response.status_code == HTTPStatus.NOT_FOUND:
            raise IdentityDirectoryError(f"The realm has no role named {role!r}")
        if response.status_code != HTTPStatus.OK:
            raise IdentityDirectoryError(
                f"Keycloak refused the role lookup ({response.status_code})"
            )
        try:
            representation = cast(object, response.json())
        except ValueError as error:
            raise IdentityDirectoryError("Keycloak returned a malformed role") from error
        if not isinstance(representation, dict):
            raise IdentityDirectoryError("Keycloak returned a malformed role")

        response = await self._request(
            "POST",
            f"{_KEYCLOAK_USERS_URL}/{_segment(subject)}/role-mappings/realm",
            [cast(dict[str, object], representation)],
        )
        if response.status_code != HTTPStatus.NO_CONTENT:
            raise IdentityDirectoryError(f"Keycloak refused the role ({response.status_code})")

    async def delete_account(self, subject: str) -> None:
        response = await self._request("DELETE", f"{_KEYCLOAK_USERS_URL}/{_segment(subject)}")
        if response.status_code not in (HTTPStatus.NO_CONTENT, HTTPStatus.NOT_FOUND):
            raise IdentityDirectoryError(f"Keycloak refused the deletion ({response.status_code})")

    async def health_check(self) -> None:
        await self._fetch_token()
