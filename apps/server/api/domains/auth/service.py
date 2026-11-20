from collections.abc import Callable
from contextlib import suppress
from datetime import datetime

from core_domain.auth import User, UserRole
from core_domain.ddd import Service, Unavailable
from core_domain.ids import UserId

from api.domains.auth.accounts import IdentityAccounts
from api.domains.auth.repository import UserRepository


class UserService(Service[UserRepository]):
    def __init__(
        self,
        repository: UserRepository,
        accounts: IdentityAccounts,
        clock: Callable[[], datetime],
    ) -> None:
        super().__init__(repository)
        self._accounts = accounts
        self._clock = clock

    async def user(self, user_id: UserId) -> User:
        return await self._repository.get(user_id)

    async def create(
        self,
        email: str,
        first_name: str,
        last_name: str,
        role: UserRole,
        expires_at: datetime | None,
    ) -> User:
        """A new user and the account they sign in with. The user's rules are checked first, so a
        refused user never reaches the identity provider, and both get the same normalised email.
        The account comes next, because the user is linked to it by its reference. If the user
        then cannot be saved, the account is removed again, so a failure leaves neither."""
        now = self._clock()
        email = User.check_new(email, first_name, last_name, role, expires_at, now)
        identity_provider_ref = await self._accounts.create(email, first_name, last_name, role)
        try:
            user = User.create(
                identity_provider_ref, email, first_name, last_name, role, expires_at, now
            )
            await self._repository.save(user)
        except Exception:
            # The original error is the one to report. A removal that fails is logged by the
            # adapter, and leaves an account with no user, which is harmless until reused.
            with suppress(Unavailable):
                await self._accounts.delete(identity_provider_ref)
            raise
        return user
