from collections.abc import Callable
from contextlib import suppress
from datetime import datetime

from core_domain.auth import User, UserRole
from core_domain.ddd import Page, Service, Unavailable, change_async
from core_domain.ids import UserId

from api.common.paging import PageSizes
from api.domains.auth.accounts import IdentityAccounts
from api.domains.auth.repository import UserRepository

PAGE_SIZES = PageSizes(default=50, maximum=100)


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

    async def page(self, page_size: int, page_token: str) -> Page[User]:
        """Every user, deleted ones included, newest first."""
        return await self._repository.page(PAGE_SIZES.size(page_size), page_token)

    async def suspend(self, user_id: UserId) -> User:
        return await self._transition(user_id, User.suspend)

    async def activate(self, user_id: UserId) -> User:
        return await self._transition(user_id, User.activate)

    async def delete(self, user_id: UserId) -> User:
        return await self._transition(user_id, User.delete)

    async def _transition(self, user_id: UserId, rule: Callable[[User, datetime], None]) -> User:
        """Applies a status rule and keeps the account's sign-in in step: enabled exactly while
        the user is active. The rule runs first, so a refused change never reaches the identity
        provider. If the user then cannot be saved, the account goes back to how it was."""
        now = self._clock()
        # The account and whether it could sign in before the change, once its access changed.
        restore: tuple[str, bool] | None = None

        async def apply(user: User) -> None:
            nonlocal restore
            could_sign_in = user.can_sign_in()
            rule(user, now)
            await self._set_access(user.identity_provider_ref, user.can_sign_in())
            restore = (user.identity_provider_ref, could_sign_in)

        try:
            return await change_async(self._repository, user_id, apply)
        except Exception:
            if restore is not None:
                # The original error is the one to report; a failed restore is logged by the
                # adapter.
                with suppress(Unavailable):
                    await self._set_access(*restore)
            raise

    async def _set_access(self, identity_provider_ref: str, can_sign_in: bool) -> None:
        """Enables or disables the account. Both are idempotent, so setting an account already
        in step is harmless."""
        if can_sign_in:
            await self._accounts.enable(identity_provider_ref)
        else:
            await self._accounts.disable(identity_provider_ref)

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
