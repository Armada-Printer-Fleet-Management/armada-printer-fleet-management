from abc import abstractmethod

from core_domain.auth import User
from core_domain.ddd import AbstractAsyncRepository, Page
from core_domain.ids import UserId


class UserRepository(AbstractAsyncRepository[UserId, User]):
    """Where the server keeps users. Implementations live in api/infrastructure, and each must
    pass tests/integration/contract/test_user_repository.py. A save raises AlreadyExists when
    another user already has the email or the identity provider subject."""

    @abstractmethod
    async def page(self, page_size: int, page_token: str) -> Page[User]:
        """Newest first. An empty token starts at the first page. Raises InvalidPageToken for a
        token this repository did not issue."""
