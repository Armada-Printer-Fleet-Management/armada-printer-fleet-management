from abc import abstractmethod

from core_domain.auth import Session, User
from core_domain.ddd import AbstractReadRepository, Page
from core_domain.ids import SessionId, UserId


class SessionRepository(AbstractReadRepository[SessionId, Session]):
    """The operator's session with the identity provider, which owns it: this app never saves
    one. Implementations live in armada_infrastructure and keep the credentials to themselves."""

    @abstractmethod
    def sign_in(self) -> Session:
        """Blocks until the operator finishes signing in. Raises SignInFailed."""

    @abstractmethod
    def sign_out(self) -> None:
        """Ends the session here and at the identity provider."""

    @abstractmethod
    def session(self) -> Session | None:
        """The current session, or None when nobody is signed in."""


class UserRepository(AbstractReadRepository[UserId, User]):
    """The people who can sign in, as the application server reports them. The desktop only reads
    them. Implementations live in armada_infrastructure."""

    @abstractmethod
    def page(self, page_size: int, page_token: str) -> Page[User]: ...
