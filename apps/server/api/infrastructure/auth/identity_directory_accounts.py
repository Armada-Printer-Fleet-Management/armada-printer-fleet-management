from collections.abc import Awaitable, Callable, Generator, Mapping
from contextlib import AsyncExitStack, contextmanager
from types import TracebackType
from typing import Self

import structlog
from core_domain.auth import UserRole
from core_domain.ddd import AlreadyExists, Unavailable
from plugin_api.identity_directory import (
    AccountExistsError,
    IdentityDirectory,
    IdentityDirectoryError,
    NewAccount,
)

from api.common.authentication import Role

logger = structlog.stdlib.get_logger(__name__)

_DEPENDENCY = "identity provider"
# The directory's role names are the ones access tokens carry, which the access policy reads.
_DIRECTORY_ROLES: Mapping[UserRole, Role] = {
    UserRole.GUEST: Role.GUEST,
    UserRole.STUDENT: Role.STUDENT,
    UserRole.STAFF: Role.STAFF,
    UserRole.ADMIN: Role.ADMIN,
}


@contextmanager
def _directory_errors() -> Generator[None]:
    try:
        yield
    except AccountExistsError as error:
        raise AlreadyExists("user", "email") from error
    except IdentityDirectoryError as error:
        raise Unavailable(_DEPENDENCY) from error


class IdentityDirectoryAccounts:
    """The auth domain's sign-in accounts in the deployment's IdentityDirectory plugin. Builds the
    directory when opened, not when constructed, so importing the app reads no configuration."""

    def __init__(self, open_directory: Callable[[], IdentityDirectory]) -> None:
        self._open_directory = open_directory
        self._exit_stack = AsyncExitStack()
        self._directory: IdentityDirectory | None = None

    async def __aenter__(self) -> Self:
        with _directory_errors():
            self._directory = await self._exit_stack.enter_async_context(self._open_directory())
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self._directory = None
        await self._exit_stack.aclose()

    def _identity_directory(self) -> IdentityDirectory:
        if self._directory is None:
            raise Unavailable(_DEPENDENCY)
        return self._directory

    async def health_check(self) -> None:
        """Raises Unavailable if the directory cannot be reached or is not open."""
        with _directory_errors():
            await self._identity_directory().health_check()

    async def create(self, email: str, first_name: str, last_name: str, role: UserRole) -> str:
        account = NewAccount(email, first_name, last_name, _DIRECTORY_ROLES[role].value)
        with _directory_errors():
            return await self._identity_directory().create_account(account)

    async def enable(self, identity_provider_ref: str) -> None:
        await self._change_access(
            identity_provider_ref,
            "enable",
            lambda directory: directory.enable_account(identity_provider_ref),
        )

    async def disable(self, identity_provider_ref: str) -> None:
        await self._change_access(
            identity_provider_ref,
            "disable",
            lambda directory: directory.disable_account(identity_provider_ref),
        )

    async def _change_access(
        self,
        identity_provider_ref: str,
        action: str,
        change: Callable[[IdentityDirectory], Awaitable[None]],
    ) -> None:
        try:
            with _directory_errors():
                await change(self._identity_directory())
        except Unavailable:
            # Logged here, because a caller restoring an account after another failure reports
            # that failure instead.
            logger.warning(
                "identity provider account access not changed",
                action=action,
                identity_provider_ref=identity_provider_ref,
                exc_info=True,
            )
            raise

    async def set_role(
        self, identity_provider_ref: str, role: UserRole, previous_role: UserRole
    ) -> None:
        try:
            with _directory_errors():
                await self._identity_directory().set_account_role(
                    identity_provider_ref,
                    _DIRECTORY_ROLES[role].value,
                    _DIRECTORY_ROLES[previous_role].value,
                )
        except Unavailable:
            # Logged here, because a caller restoring an account after another failure reports
            # that failure instead.
            logger.warning(
                "identity provider account role not changed",
                role=role.name,
                previous_role=previous_role.name,
                identity_provider_ref=identity_provider_ref,
                exc_info=True,
            )
            raise

    async def delete(self, identity_provider_ref: str) -> None:
        try:
            with _directory_errors():
                await self._identity_directory().delete_account(identity_provider_ref)
        except Unavailable:
            # Logged here, because a caller removing an account after another failure reports
            # that failure instead.
            logger.warning(
                "identity provider account not deleted",
                identity_provider_ref=identity_provider_ref,
                exc_info=True,
            )
            raise
