from dataclasses import dataclass
from types import TracebackType
from typing import Protocol, Self


@dataclass(frozen=True)
class NewAccount:
    """
    An account to create in an identity directory.

    `role` is the name of the directory role the account is given, such as "staff".
    """

    email: str
    first_name: str
    last_name: str
    role: str


class IdentityDirectory(Protocol):
    """
    A protocol for an identity directory: the system that holds the accounts people sign in with.

    Any error with the directory itself will raise an IdentityDirectoryError. If an account with
    the same email already exists, an AccountExistsError will be raised.
    A subject is the directory's own ID for an account. Callers treat it as an opaque string.

    A directory is opened with `async with` before use and closed when that block exits, so
    whoever owns it can manage its lifetime without knowing which directory it is.
    """

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...

    async def create_account(self, account: NewAccount) -> str:
        """
        Create an account with its role and return its subject.

        If creation fails part way, the directory removes whatever it created before raising, so a
        failed call leaves no account behind.

        Raises AccountExistsError if an account with the same email already exists.
        Raises IdentityDirectoryError if there is an error with the directory itself.
        """
        ...

    async def delete_account(self, subject: str) -> None:
        """
        Delete the account with this subject. Deleting an account that does not exist succeeds.

        Raises IdentityDirectoryError if there is an error with the directory itself.
        """
        ...

    async def enable_account(self, subject: str) -> None:
        """
        Let the account with this subject sign in.

        Raises IdentityDirectoryError if there is no such account, or if there is an error with
        the directory itself.
        """
        ...

    async def disable_account(self, subject: str) -> None:
        """
        Stop the account with this subject signing in, and end its sessions. Disabling an account
        that does not exist succeeds.

        Raises IdentityDirectoryError if there is an error with the directory itself.
        """
        ...

    async def set_account_role(self, subject: str, role: str, previous_role: str) -> None:
        """
        Give the account with this subject `role` in place of `previous_role`, and end its
        sessions so its next sign-in carries the new role. The account's other roles are kept.
        When `role` and `previous_role` are the same, the account keeps that role.

        If the role cannot be swapped, the account's roles are left as they were.

        Raises IdentityDirectoryError if there is no such account, if either role does not exist,
        or if there is an error with the directory itself.
        """
        ...

    async def health_check(self) -> None:
        """
        Check the health of the directory.

        Raises IdentityDirectoryError if the directory is not healthy.
        """
        ...


class IdentityDirectoryError(Exception):
    """An error with the identity directory itself."""


class AccountExistsError(IdentityDirectoryError):
    """An account with the same email already exists."""
