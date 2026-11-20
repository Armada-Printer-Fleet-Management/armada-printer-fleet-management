from collections.abc import AsyncIterator

import pytest
from core_domain.auth import User, UserRole, UserStatus
from core_domain.ddd import AlreadyExists, EntityNotFound, RuleViolation, Unavailable
from core_domain.ids import UserId

from api.domains.auth.service import UserService
from api.infrastructure.auth.identity_directory_accounts import IdentityDirectoryAccounts
from api.infrastructure.dev_data import STUB_STAFF_ID, stub_users
from api.infrastructure.user_memory import InMemoryUserRepository
from tests.fakes import MemoryIdentityDirectory
from tests.samples import NOW

# A seeded user's email, so the database refuses it while the directory has no account.
SEEDED_EMAIL = next(user.email for user in stub_users() if user.id == STUB_STAFF_ID)


@pytest.fixture
def directory() -> MemoryIdentityDirectory:
    return MemoryIdentityDirectory()


@pytest.fixture
async def service(directory: MemoryIdentityDirectory) -> AsyncIterator[UserService]:
    async with IdentityDirectoryAccounts(lambda: directory) as accounts:
        yield UserService(InMemoryUserRepository(stub_users()), accounts, clock=lambda: NOW)


async def test_user_reports_an_unknown_id(service: UserService) -> None:
    with pytest.raises(EntityNotFound):
        await service.user(UserId.new())


# Creating a user


async def create(
    service: UserService,
    email: str = "new@example.com",
    role: UserRole = UserRole.STUDENT,
) -> User:
    return await service.create(email, "First", "Last", role, None)


async def test_create_saves_an_active_user_linked_to_a_new_account(
    service: UserService, directory: MemoryIdentityDirectory
) -> None:
    user = await create(service)

    assert user.status is UserStatus.ACTIVE
    assert list(directory.accounts) == [user.identity_provider_ref]
    assert await service.user(user.id) == user


async def test_the_account_gets_the_same_normalised_email_as_the_user(
    service: UserService, directory: MemoryIdentityDirectory
) -> None:
    user = await create(service, email="  New.Person@Example.COM ")

    assert user.email == "new.person@example.com"
    assert directory.accounts[user.identity_provider_ref].email == user.email


async def test_a_user_the_rules_refuse_leaves_no_account(
    service: UserService, directory: MemoryIdentityDirectory
) -> None:
    with pytest.raises(RuleViolation):
        await create(service, role=UserRole.GUEST)

    assert directory.accounts == {}


class _UnavailableSave(InMemoryUserRepository):
    async def save(self, entity: User) -> None:
        raise Unavailable("database")


async def test_a_duplicate_email_in_the_database_leaves_no_account(
    service: UserService, directory: MemoryIdentityDirectory
) -> None:
    with pytest.raises(AlreadyExists):
        await create(service, email=SEEDED_EMAIL)

    assert directory.accounts == {}


async def test_a_save_outage_leaves_no_account(directory: MemoryIdentityDirectory) -> None:
    async with IdentityDirectoryAccounts(lambda: directory) as accounts:
        service = UserService(_UnavailableSave(), accounts, clock=lambda: NOW)

        with pytest.raises(Unavailable, match="database"):
            await create(service)

    assert directory.accounts == {}


class _SaveThatBreaksTheDirectory(InMemoryUserRepository):
    """Refuses the save, and takes the directory down first, so removing the account fails too."""

    def __init__(self, directory: MemoryIdentityDirectory) -> None:
        super().__init__()
        self._directory = directory

    async def save(self, entity: User) -> None:
        self._directory.healthy = False
        raise AlreadyExists("user", "email")


async def test_a_failed_account_removal_still_reports_the_original_error(
    directory: MemoryIdentityDirectory,
) -> None:
    async with IdentityDirectoryAccounts(lambda: directory) as accounts:
        service = UserService(_SaveThatBreaksTheDirectory(directory), accounts, lambda: NOW)

        with pytest.raises(AlreadyExists):
            await create(service)
