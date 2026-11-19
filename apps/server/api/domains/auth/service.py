from collections.abc import Callable
from datetime import datetime

from core_domain.auth import User
from core_domain.ddd import Service
from core_domain.ids import UserId

from api.domains.auth.repository import UserRepository


class UserService(Service[UserRepository]):
    def __init__(self, repository: UserRepository, clock: Callable[[], datetime]) -> None:
        super().__init__(repository)
        self._clock = clock

    async def user(self, user_id: UserId) -> User:
        return await self._repository.get(user_id)
