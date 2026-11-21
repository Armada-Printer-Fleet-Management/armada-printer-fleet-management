from collections.abc import AsyncIterator, Awaitable, Callable

import pytest
from core_domain.auth import User, UserRole, UserStatus
from core_domain.ddd import AlreadyExists, EntityNotFound, RuleViolation, Unavailable
from core_domain.ids import UserId

from api.domains.auth.service import PAGE_SIZES, UserService
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


# Suspending, activating and deleting a user


async def test_suspend_disables_the_account(
    service: UserService, directory: MemoryIdentityDirectory
) -> None:
    user = await create(service)

    suspended = await service.suspend(user.id)

    assert suspended.status is UserStatus.SUSPENDED
    assert await service.user(user.id) == suspended
    assert directory.disabled == {user.identity_provider_ref}


async def test_delete_disables_the_account(
    service: UserService, directory: MemoryIdentityDirectory
) -> None:
    user = await create(service)

    deleted = await service.delete(user.id)

    assert deleted.status is UserStatus.DELETED
    assert deleted.deleted_at == NOW
    assert directory.disabled == {user.identity_provider_ref}


@pytest.mark.parametrize("hide", [UserService.suspend, UserService.delete])
async def test_activate_enables_the_account(
    service: UserService,
    directory: MemoryIdentityDirectory,
    hide: Callable[[UserService, UserId], Awaitable[User]],
) -> None:
    user = await create(service)
    await hide(service, user.id)

    activated = await service.activate(user.id)

    assert activated.status is UserStatus.ACTIVE
    assert activated.deleted_at is None
    assert directory.disabled == set()


async def test_deleting_a_suspended_user_keeps_the_account_disabled(
    service: UserService, directory: MemoryIdentityDirectory
) -> None:
    user = await create(service)
    await service.suspend(user.id)

    await service.delete(user.id)

    assert directory.disabled == {user.identity_provider_ref}


async def test_a_refused_transition_changes_neither_user_nor_account(
    service: UserService, directory: MemoryIdentityDirectory
) -> None:
    user = await create(service)

    with pytest.raises(RuleViolation):
        await service.activate(user.id)

    assert await service.user(user.id) == user
    assert directory.disabled == set()


@pytest.mark.parametrize(
    "transition", [UserService.suspend, UserService.activate, UserService.delete]
)
async def test_a_transition_reports_an_unknown_id(
    service: UserService, transition: Callable[[UserService, UserId], Awaitable[User]]
) -> None:
    with pytest.raises(EntityNotFound):
        await transition(service, UserId.new())


async def test_an_unreachable_directory_leaves_the_user_unchanged(
    service: UserService, directory: MemoryIdentityDirectory
) -> None:
    user = await create(service)
    directory.healthy = False

    with pytest.raises(Unavailable, match="identity provider"):
        await service.suspend(user.id)

    assert await service.user(user.id) == user


class _SwitchableSave(InMemoryUserRepository):
    """Saves until `fail` is set, then refuses every save as an outage."""

    fail = False

    async def save(self, entity: User) -> None:
        if self.fail:
            raise Unavailable("database")
        await super().save(entity)


@pytest.mark.parametrize(
    ("setup", "transition", "disabled_after"),
    [
        (None, UserService.suspend, False),
        (None, UserService.delete, False),
        (UserService.suspend, UserService.activate, True),
    ],
    ids=["suspend", "delete", "activate"],
)
async def test_a_failed_save_puts_the_account_back_as_it_was(
    directory: MemoryIdentityDirectory,
    setup: Callable[[UserService, UserId], Awaitable[User]] | None,
    transition: Callable[[UserService, UserId], Awaitable[User]],
    disabled_after: bool,
) -> None:
    repository = _SwitchableSave()
    async with IdentityDirectoryAccounts(lambda: directory) as accounts:
        service = UserService(repository, accounts, clock=lambda: NOW)
        user = await create(service)
        if setup is not None:
            await setup(service, user.id)
        before = await service.user(user.id)
        repository.fail = True

        with pytest.raises(Unavailable, match="database"):
            await transition(service, user.id)

        assert await service.user(user.id) == before
    assert (user.identity_provider_ref in directory.disabled) is disabled_after


# Listing users


@pytest.mark.parametrize(
    ("requested", "applied"),
    [(0, PAGE_SIZES.default), (2, 2), (PAGE_SIZES.maximum + 1, PAGE_SIZES.maximum)],
)
async def test_page_applies_the_default_and_the_cap(
    directory: MemoryIdentityDirectory, requested: int, applied: int
) -> None:
    users = [
        User.create(
            f"ref-{n}", f"user-{n}@example.com", "First", "Last", UserRole.STUDENT, None, NOW
        )
        for n in range(PAGE_SIZES.maximum + 1)
    ]
    async with IdentityDirectoryAccounts(lambda: directory) as accounts:
        service = UserService(InMemoryUserRepository(users), accounts, clock=lambda: NOW)

        assert len((await service.page(requested, "")).items) == applied
