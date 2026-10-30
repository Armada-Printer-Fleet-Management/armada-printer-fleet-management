"""OidcTokenVerifier against a fake provider served through httpx2.MockTransport, so tokens are
signed and verified for real without a network."""

import asyncio
import time
from collections.abc import Callable, Coroutine, Mapping

import httpx2
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm
from plugin_api.token_verifier import InvalidTokenError, TokenVerifier, TokenVerifierError

from auth_oidc import OidcTokenVerifier

ISSUER = "https://example.test/realms/test"
AUDIENCE = "test-server"
JWKS_URL = "https://example.test/certs"
ROLES_CLAIM = "realm_access.roles"
KID = "key-1"

# Generated once: an RSA key takes a noticeable moment to make.
SIGNING_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
UNPUBLISHED_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def public_jwk(private_key: rsa.RSAPrivateKey, kid: str) -> dict[str, object]:
    jwk = RSAAlgorithm.to_jwk(private_key.public_key(), as_dict=True)
    return {**jwk, "kid": kid, "use": "sig", "alg": "RS256"}


def token(
    claims: Mapping[str, object] | None = None,
    *,
    key: rsa.RSAPrivateKey | str = SIGNING_KEY,
    algorithm: str = "RS256",
    headers: dict[str, str] | None = None,
) -> str:
    """A token valid for the fake provider, with `claims` replacing or adding to the defaults."""
    now = int(time.time())
    payload: dict[str, object] = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "sub": "subject-1",
        "iat": now,
        "exp": now + 60,
        "realm_access": {"roles": ["student", "staff"]},
    }
    payload.update(claims or {})
    return jwt.encode(
        payload, key, algorithm=algorithm, headers={"kid": KID} if headers is None else headers
    )


class FakeProvider:
    """Serves a JWKS and counts the requests for it. `respond` can be replaced to fail."""

    def __init__(self) -> None:
        self.requests = 0
        self.respond: Callable[[httpx2.Request], httpx2.Response] = lambda _: httpx2.Response(
            200, json={"keys": [public_jwk(SIGNING_KEY, KID)]}
        )

    def handle(self, request: httpx2.Request) -> httpx2.Response:
        self.requests += 1
        return self.respond(request)

    def verifier(self) -> OidcTokenVerifier:
        return OidcTokenVerifier(
            issuer=ISSUER,
            audience=AUDIENCE,
            jwks_url=JWKS_URL,
            roles_claim=ROLES_CLAIM,
            transport=httpx2.MockTransport(self.handle),
        )


type Use[T] = Callable[[OidcTokenVerifier], Coroutine[object, object, T]]


def run[T](provider: FakeProvider, use: Use[T]) -> T:
    """Opens a verifier over the provider and runs `use` with it."""

    async def opened() -> T:
        async with provider.verifier() as verifier:
            return await use(verifier)

    return asyncio.run(opened())


def refused(request: httpx2.Request) -> httpx2.Response:
    raise httpx2.ConnectError("connection refused", request=request)


def test_satisfies_the_token_verifier_port() -> None:
    verifier: TokenVerifier = FakeProvider().verifier()
    assert verifier is not None


# Accepting valid tokens


def test_a_valid_token_gives_its_subject_and_roles() -> None:
    verified = run(FakeProvider(), lambda verifier: verifier.verify(token()))

    assert verified.subject == "subject-1"
    assert verified.roles == {"student", "staff"}


def test_a_token_without_the_roles_claim_has_no_roles() -> None:
    verified = run(FakeProvider(), lambda verifier: verifier.verify(token({"realm_access": None})))

    assert verified.roles == frozenset()


def test_roles_that_are_not_strings_are_dropped() -> None:
    roles = token({"realm_access": {"roles": ["student", 3, {"name": "staff"}]}})

    verified = run(FakeProvider(), lambda verifier: verifier.verify(roles))

    assert verified.roles == {"student"}


# Rejecting bad tokens


@pytest.mark.parametrize(
    "claims",
    [{"exp": int(time.time()) - 60}, {"aud": "another-server"}, {"iss": "https://elsewhere.test"}],
    ids=["expired", "wrong audience", "wrong issuer"],
)
def test_a_token_failing_a_claim_check_is_rejected(claims: dict[str, object]) -> None:
    with pytest.raises(InvalidTokenError):
        run(FakeProvider(), lambda verifier: verifier.verify(token(claims)))


def test_a_token_signed_by_an_unpublished_key_is_rejected() -> None:
    with pytest.raises(InvalidTokenError):
        run(FakeProvider(), lambda verifier: verifier.verify(token(key=UNPUBLISHED_KEY)))


@pytest.mark.parametrize(
    "headers", [{"kid": "unknown-key"}, {}], ids=["unknown kid", "missing kid"]
)
def test_a_token_without_a_matching_kid_is_rejected(headers: dict[str, str]) -> None:
    with pytest.raises(InvalidTokenError):
        run(FakeProvider(), lambda verifier: verifier.verify(token(headers=headers)))


def test_a_string_that_is_not_a_token_is_rejected() -> None:
    with pytest.raises(InvalidTokenError):
        run(FakeProvider(), lambda verifier: verifier.verify("not-a-token"))


def test_a_token_using_another_algorithm_is_rejected() -> None:
    hs256 = token(key="a-shared-secret-at-least-32-bytes-long", algorithm="HS256")

    with pytest.raises(InvalidTokenError):
        run(FakeProvider(), lambda verifier: verifier.verify(hs256))


# Signing key cache


def test_signing_keys_are_downloaded_once() -> None:
    provider = FakeProvider()

    async def verify_twice(verifier: OidcTokenVerifier) -> None:
        await verifier.verify(token())
        await verifier.verify(token())

    run(provider, verify_twice)

    assert provider.requests == 1


def test_an_unknown_kid_downloads_the_keys_again_once() -> None:
    provider = FakeProvider()

    async def verify_unknown_kid(verifier: OidcTokenVerifier) -> None:
        await verifier.verify(token())
        with pytest.raises(InvalidTokenError):
            await verifier.verify(token(headers={"kid": "unknown-key"}))

    run(provider, verify_unknown_kid)

    assert provider.requests == 2


# Provider failures and lifetime


def test_an_unreachable_provider_is_a_verifier_error_not_an_invalid_token() -> None:
    provider = FakeProvider()
    provider.respond = refused

    with pytest.raises(TokenVerifierError) as raised:
        run(provider, lambda verifier: verifier.verify(token()))

    assert not isinstance(raised.value, InvalidTokenError)


@pytest.mark.parametrize(
    "response",
    [
        httpx2.Response(500),
        httpx2.Response(200, text="not json"),
        httpx2.Response(200, json={"keys": []}),
    ],
    ids=["server error", "not json", "no keys"],
)
def test_an_unusable_key_set_is_a_verifier_error(response: httpx2.Response) -> None:
    provider = FakeProvider()
    provider.respond = lambda _: response

    with pytest.raises(TokenVerifierError) as raised:
        run(provider, lambda verifier: verifier.verify(token()))

    assert not isinstance(raised.value, InvalidTokenError)


def test_health_check_passes_when_the_keys_are_served() -> None:
    run(FakeProvider(), lambda verifier: verifier.health_check())


def test_health_check_fails_when_the_provider_is_unreachable() -> None:
    provider = FakeProvider()
    provider.respond = refused

    with pytest.raises(TokenVerifierError):
        run(provider, lambda verifier: verifier.health_check())


def test_verifying_before_opening_is_a_verifier_error() -> None:
    with pytest.raises(TokenVerifierError):
        asyncio.run(FakeProvider().verifier().verify(token()))
