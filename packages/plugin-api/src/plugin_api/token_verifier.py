from dataclasses import dataclass
from types import TracebackType
from typing import Protocol, Self


@dataclass(frozen=True)
class VerifiedToken:
    """
    A verified token.

    This is returned by a TokenVerifier after verifying a token.
    """

    subject: str
    roles: frozenset[str]


class TokenVerifier(Protocol):
    """
    A protocol for a token verifier.

    Any error with the verifier itself will raise a TokenVerifierError. If a token is invalid, an
    InvalidTokenError will be raised.
    A token is a string chosen by the caller. The verifier treats it as an opaque string.

    A verifier is opened with `async with` before use and closed when that block exits, so whoever
    owns it can manage its lifetime without knowing which verifier it is.

    """

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...

    async def verify(self, token: str) -> VerifiedToken:
        """
        Verify a token and return the verified token.

        Raises InvalidTokenError if the token is invalid.
        Raises TokenVerifierError if there is an error with the verifier itself.
        """
        ...

    async def health_check(self) -> None:
        """
        Check the health of the verifier.

        Raises TokenVerifierError if the verifier is not healthy.
        """
        ...


class TokenVerifierError(Exception):
    """An error with the token verifier itself."""


class InvalidTokenError(TokenVerifierError):
    """The token is invalid."""
