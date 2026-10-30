from dataclasses import FrozenInstanceError

import pytest

from plugin_api.token_verifier import InvalidTokenError, TokenVerifierError, VerifiedToken


def test_an_invalid_token_is_a_token_verifier_error() -> None:
    """Code that handles any verification failure also handles a rejected token."""
    assert issubclass(InvalidTokenError, TokenVerifierError)


def test_a_verified_token_cannot_be_changed() -> None:
    token = VerifiedToken(subject="subject", roles=frozenset({"student"}))

    with pytest.raises(FrozenInstanceError):
        token.subject = "someone else"  # pyright: ignore[reportAttributeAccessIssue]
