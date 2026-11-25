from collections.abc import Callable, Coroutine

import pytest
from core_domain.auth import UserRole
from core_domain.ddd import AlreadyExists, Unavailable

from api.infrastructure.auth.identity_directory_accounts import IdentityDirectoryAccounts
from tests.fakes import MemoryIdentityDirectory

type Use[T] = Callable[[IdentityDirectoryAccounts], Coroutine[object, object, T]]


async def use_accounts[T](directory: MemoryIdentityDirectory, use: Use[T]) -> T:
    async with IdentityDirectoryAccounts(lambda: directory) as accounts:
        return await use(accounts)


async def _create(accounts: IdentityDirectoryAccounts, role: UserRole = UserRole.STUDENT) -> str:
    return await accounts.create("person@example.com", "First", "Last", role)


@pytest.mark.parametrize(
    ("role", "directory_role"),
    [
        (UserRole.GUEST, "guest"),
        (UserRole.STUDENT, "student"),
        (UserRole.STAFF, "staff"),
        (UserRole.ADMIN, "admin"),
    ],
)
async def test_an_account_gets_the_role_name_tokens_carry(
    role: UserRole, directory_role: str
) -> None:
    directory = MemoryIdentityDirectory()

    reference = await use_accounts(directory, lambda accounts: _create(accounts, role))

    assert directory.accounts[reference].role == directory_role


async def test_an_existing_email_already_exists() -> None:
    directory = MemoryIdentityDirectory()
    await use_accounts(directory, _create)

    with pytest.raises(AlreadyExists) as raised:
        await use_accounts(directory, _create)

    assert str(raised.value) == "A user with this email already exists"


async def _delete(accounts: IdentityDirectoryAccounts) -> None:
    await accounts.delete("identity-provider-ref")


async def _health_check(accounts: IdentityDirectoryAccounts) -> None:
    await accounts.health_check()


async def _disable(accounts: IdentityDirectoryAccounts) -> None:
    await accounts.disable("identity-provider-ref")


async def test_disable_then_enable_changes_the_accounts_access() -> None:
    directory = MemoryIdentityDirectory()

    async def use(accounts: IdentityDirectoryAccounts) -> tuple[str, bool]:
        reference = await _create(accounts)
        await accounts.disable(reference)
        disabled = reference in directory.disabled
        await accounts.enable(reference)
        return reference, disabled

    reference, disabled = await use_accounts(directory, use)

    assert disabled
    assert reference not in directory.disabled


async def test_enabling_an_account_that_does_not_exist_is_unavailable() -> None:
    with pytest.raises(Unavailable, match="identity provider"):
        await use_accounts(
            MemoryIdentityDirectory(),
            lambda accounts: accounts.enable("identity-provider-ref"),
        )


@pytest.mark.parametrize(
    "use",
    [_create, _delete, _disable, _health_check],
    ids=["create", "delete", "disable", "health_check"],
)
async def test_an_unreachable_directory_is_unavailable(use: Use[object]) -> None:
    directory = MemoryIdentityDirectory()
    directory.healthy = False

    with pytest.raises(Unavailable, match="identity provider"):
        await use_accounts(directory, use)
