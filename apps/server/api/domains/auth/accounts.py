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
