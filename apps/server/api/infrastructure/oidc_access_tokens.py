from collections.abc import Callable, Generator
from contextlib import AsyncExitStack, contextmanager
from types import TracebackType
from typing import Self

from core_domain.ddd import Unavailable
from plugin_api.token_verifier import InvalidTokenError, TokenVerifier, TokenVerifierError

from api.common.authentication import Caller, InvalidAccessToken, Role

_DEPENDENCY = "identity provider"


@contextmanager
def _verifier_errors() -> Generator[None]:
    try:
        yield
    except InvalidTokenError as error:
        raise InvalidAccessToken from error
    except TokenVerifierError as error:
        raise Unavailable(_DEPENDENCY) from error


def _roles(names: frozenset[str]) -> frozenset[Role]:
    # Providers add roles of their own, such as offline_access, which mean nothing here.
    return frozenset(Role(name) for name in names if name in Role)


class OidcAccessTokens:
    """Access tokens checked by the deployment's TokenVerifier plugin. Builds the verifier when
    opened, not when constructed, so importing the app reads no configuration."""

    def __init__(self, open_token_verifier: Callable[[], TokenVerifier]) -> None:
        self._open_token_verifier = open_token_verifier
        self._exit_stack = AsyncExitStack()
        self._token_verifier: TokenVerifier | None = None

    async def __aenter__(self) -> Self:
        with _verifier_errors():
            self._token_verifier = await self._exit_stack.enter_async_context(
                self._open_token_verifier()
            )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self._token_verifier = None
        await self._exit_stack.aclose()

    def _verifier(self) -> TokenVerifier:
        if self._token_verifier is None:
            raise Unavailable(_DEPENDENCY)
        return self._token_verifier

    async def verify(self, token: str) -> Caller:
        """The caller the token names. Raises InvalidAccessToken if the token is rejected, and
        Unavailable if the identity provider cannot be reached."""
        with _verifier_errors():
            verified = await self._verifier().verify(token)
        return Caller(subject=verified.subject, roles=_roles(verified.roles))

    async def health_check(self) -> None:
        """Raises Unavailable if the identity provider cannot be reached or is not open."""
        with _verifier_errors():
            await self._verifier().health_check()
