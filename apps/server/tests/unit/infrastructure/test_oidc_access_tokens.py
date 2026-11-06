import asyncio
from collections.abc import Callable, Coroutine

import pytest
from core_domain.ddd import Unavailable
from plugin_api.token_verifier import InvalidTokenError, TokenVerifierError, VerifiedToken

from api.common.authentication import Caller, InvalidAccessToken, Role
from api.infrastructure.oidc_access_tokens import OidcAccessTokens
from tests.fakes import FakeTokenVerifier

type Use[T] = Callable[[OidcAccessTokens], Coroutine[object, object, T]]


def run[T](verifier: FakeTokenVerifier, use: Use[T]) -> T:
    async def opened() -> T:
        async with OidcAccessTokens(lambda: verifier) as tokens:
            return await use(tokens)

    return asyncio.run(opened())


def test_a_verified_token_becomes_a_caller_without_unknown_roles() -> None:
    verifier = FakeTokenVerifier(
        VerifiedToken("subject-1", frozenset({"student", "offline_access", "default-roles"}))
    )

    caller = run(verifier, lambda tokens: tokens.verify("token"))

    assert caller == Caller("subject-1", frozenset({Role.STUDENT}))


def test_a_rejected_token_is_an_invalid_access_token() -> None:
    verifier = FakeTokenVerifier(VerifiedToken("subject-1", frozenset()), InvalidTokenError())

    with pytest.raises(InvalidAccessToken):
        run(verifier, lambda tokens: tokens.verify("token"))


@pytest.mark.parametrize(
    "use",
    [lambda tokens: tokens.verify("token"), lambda tokens: tokens.health_check()],
    ids=["verify", "health_check"],
)
def test_an_unreachable_provider_is_unavailable(use: Use[object]) -> None:
    verifier = FakeTokenVerifier(VerifiedToken("subject-1", frozenset()), TokenVerifierError())

    with pytest.raises(Unavailable, match="identity provider"):
        run(verifier, use)
