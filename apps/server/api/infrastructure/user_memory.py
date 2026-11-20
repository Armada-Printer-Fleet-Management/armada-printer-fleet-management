# Keeps users in process memory, for tests that need a UserRepository without Postgres.
# The server uses SqlUserRepository; both pass tests/integration/contract/test_user_repository.py.
from collections.abc import Iterable
from dataclasses import replace

from core_domain.auth import User
from core_domain.ddd import AlreadyExists, EntityNotFound, Page
from core_domain.ids import UserId

from api.domains.auth.repository import UserRepository
from api.infrastructure.page import newest_first_page


class InMemoryUserRepository(UserRepository):
    def __init__(self, users: Iterable[User] = ()) -> None:
        self._users = {user.id: user for user in users}

    async def get(self, entity_id: UserId) -> User:
        if entity_id not in self._users:
            raise EntityNotFound(entity_id)
        # A copy, as a database would return, so a change is only stored once it is saved.
        return replace(self._users[entity_id])

    async def save(self, entity: User) -> None:
        others = [user for user in self._users.values() if user.id != entity.id]
        if any(user.email == entity.email for user in others):
            raise AlreadyExists("user", "email")
        if any(user.identity_provider_ref == entity.identity_provider_ref for user in others):
            raise AlreadyExists("user", "identity provider reference")
        self._users[entity.id] = replace(entity)

    async def page(self, page_size: int, page_token: str) -> Page[User]:
        page = newest_first_page(self._users.values(), page_size, page_token)
        return Page([replace(user) for user in page.items], page.next_page_token)
