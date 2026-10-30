from types import TracebackType
from typing import Self, cast

import httpx2
import jwt
from plugin_api.token_verifier import InvalidTokenError, TokenVerifierError, VerifiedToken


def _member(value: object, name: str) -> object:
    """A JSON object's member, or None when value is not an object."""
    if isinstance(value, dict):
        return cast(dict[str, object], value).get(name)
    return None


class OidcTokenVerifier:
    def __init__(
        self,
        *,
        issuer: str,
        audience: str,
        jwks_url: str,
        roles_claim: str,
        transport: httpx2.AsyncBaseTransport | None = None,
    ) -> None:
        self._issuer = issuer
        self._audience = audience
        self._jwks_url = jwks_url
        self._roles_claim = roles_claim
        self._transport = transport
        self._client: httpx2.AsyncClient | None = None
        self._keys: jwt.PyJWKSet | None = None

    def _http(self) -> httpx2.AsyncClient:
        if self._client is None:
            raise TokenVerifierError("OIDC client is not initialized")
        return self._client

    async def _fetch_keys(self) -> jwt.PyJWKSet:
        try:
            response = await self._http().get(self._jwks_url)
            response.raise_for_status()
            return jwt.PyJWKSet.from_dict(response.json())
        except (httpx2.HTTPError, ValueError, jwt.PyJWKSetError) as error:
            raise TokenVerifierError("Failed to fetch JWKS") from error

    async def _signing_key(self, kid: str) -> jwt.PyJWK:
        if self._keys is None:
            self._keys = await self._fetch_keys()

        try:
            return self._keys[kid]
        except KeyError:
            # retry once if cache is stale, as the key may have rotated since the last fetch
            self._keys = await self._fetch_keys()

        try:
            return self._keys[kid]
        except KeyError:
            raise InvalidTokenError("No signing key matches this token") from None

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
        if client is not None:
            await client.aclose()

    async def verify(self, token: str) -> VerifiedToken:
        try:
            kid = jwt.get_unverified_header(token).get("kid")
            if not isinstance(kid, str):
                raise InvalidTokenError("token rejected")
            key = await self._signing_key(kid)
            claims = jwt.decode(
                token,
                key,
                # Fixed, never read from the token, so a token cannot pick a weaker algorithm.
                algorithms=["RS256"],
                audience=self._audience,
                issuer=self._issuer,
                options={"require": ["exp", "iat", "sub"]},
            )
        except jwt.PyJWTError as error:
            raise InvalidTokenError("token rejected") from error
        return VerifiedToken(subject=str(claims["sub"]), roles=self._roles(claims))

    def _roles(self, claims: dict[str, object]) -> frozenset[str]:
        """The roles at the dotted roles_claim path. A token without them has no roles."""
        value: object = claims
        for name in self._roles_claim.split("."):
            value = _member(value, name)
        if not isinstance(value, list):
            return frozenset()
        return frozenset(role for role in cast(list[object], value) if isinstance(role, str))

    async def health_check(self) -> None:
        self._keys = await self._fetch_keys()
