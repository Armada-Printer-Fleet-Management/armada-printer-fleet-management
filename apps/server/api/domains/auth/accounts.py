from typing import Protocol

from core_domain.auth import UserRole


class IdentityAccounts(Protocol):
    """The accounts people sign in with, held by the identity provider rather than the database.
    Implementations are in api/infrastructure."""

    async def create(self, email: str, first_name: str, last_name: str, role: UserRole) -> str:
        """Creates an account with the role and returns its identity provider reference. Raises
        AlreadyExists if an account has this email. A failed call leaves no account behind."""
        ...

    async def delete(self, identity_provider_ref: str) -> None:
        """Removes the account, if there is one."""
        ...

    async def enable(self, identity_provider_ref: str) -> None:
        """Lets the account sign in. Raises Unavailable if the identity provider cannot, including
        when there is no such account."""
        ...

    async def set_role(
        self, identity_provider_ref: str, role: UserRole, previous_role: UserRole
    ) -> None:
        """Gives the account role in place of previous_role and ends its sessions, so its next
        token carries the new role. Raises Unavailable if the identity provider cannot, including
        when there is no such account."""
        ...

    async def disable(self, identity_provider_ref: str) -> None:
        """Stops the account signing in and ends its sessions; succeeds when there is no account.
        Raises Unavailable if the identity provider cannot."""
        ...
