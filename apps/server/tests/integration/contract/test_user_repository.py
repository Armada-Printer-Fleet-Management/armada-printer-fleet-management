"""What every UserRepository must do, whatever stores the users. A new adapter joins by adding its
factory to ADAPTERS. A factory is given the test's request, so one that needs a database can ask
for the empty_database fixture."""

import base64
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from core_domain.auth import User, UserRole, UserStatus
from core_domain.ddd import AlreadyExists, EntityNotFound, InvalidPageToken
from core_domain.ids import UserId

from api.domains.auth.repository import UserRepository
from api.infrastructure.postgres_database import PostgresDatabase
from api.infrastructure.user_memory import InMemoryUserRepository
from api.infrastructure.user_sql import SqlUserRepository

type Factory = Callable[[pytest.FixtureRequest], UserRepository]


def _memory(request: pytest.FixtureRequest) -> UserRepository:
    return InMemoryUserRepository()


def _sql(request: pytest.FixtureRequest) -> UserRepository:
    database: PostgresDatabase = request.getfixturevalue("empty_database")
    return SqlUserRepository(database)


ADAPTERS = [
    pytest.param(_memory, id="memory"),
    pytest.param(_sql, id="sql"),
]
START = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)


@pytest.fixture(params=ADAPTERS)
def repository(request: pytest.FixtureRequest) -> UserRepository:
    factory: Factory = request.param
    return factory(request)


def user(minutes: int = 0) -> User:
    """A guest with every field set."""
    time = START + timedelta(minutes=minutes)
    return User(
        id=UserId.new(),
        identity_provider_ref=str(uuid4()),
        email=f"user{minutes}@example.com",
        first_name="First",
        last_name="Last",
        role=UserRole.GUEST,
        status=UserStatus.SUSPENDED,
        created_at=time,
        updated_at=time,
        expires_at=time + timedelta(days=1),
        last_login_at=time,
        deleted_at=time,
    )


async def saved(repository: UserRepository, count: int) -> list[User]:
    users = [user(minutes) for minutes in range(count)]
    for each in users:
        await repository.save(each)
    return users


async def test_get_reports_an_unknown_id(repository: UserRepository) -> None:
    with pytest.raises(EntityNotFound):
        await repository.get(UserId.new())


async def test_save_then_get_round_trips_every_field(repository: UserRepository) -> None:
    original = user()
    await repository.save(original)
    assert vars(await repository.get(original.id)) == vars(original)


async def test_a_second_save_overwrites_the_first(repository: UserRepository) -> None:
    original = user()
    await repository.save(original)

    loaded = await repository.get(original.id)
    loaded.first_name = "Changed"
    await repository.save(loaded)

    assert (await repository.get(original.id)).first_name == "Changed"


async def test_page_returns_newest_first_and_ends_with_an_empty_token(
    repository: UserRepository,
) -> None:
    users = await saved(repository, 5)

    first = await repository.page(2, "")
    second = await repository.page(2, first.next_page_token)
    last = await repository.page(2, second.next_page_token)

    paged = [each.id for page in (first, second, last) for each in page.items]
    assert paged == [each.id for each in reversed(users)]
    assert first.next_page_token and second.next_page_token
    assert last.next_page_token == ""


@pytest.mark.parametrize(
    "token",
    [
        "not a token",
        "bm9wZQ==",
        "%%%",
        # A timestamp with no UTC offset.
        base64.urlsafe_b64encode(f"2026-10-01T09:00:00|{uuid4()}".encode()).decode(),
    ],
)
async def test_page_rejects_a_token_it_did_not_issue(
    repository: UserRepository, token: str
) -> None:
    with pytest.raises(InvalidPageToken):
        await repository.page(10, token)


async def test_a_duplicate_email_is_refused_and_not_stored(repository: UserRepository) -> None:
    original = user()
    await repository.save(original)
    duplicate = user()
    duplicate.email = original.email

    with pytest.raises(AlreadyExists) as raised:
        await repository.save(duplicate)

    assert raised.value.field == "email"
    with pytest.raises(EntityNotFound):
        await repository.get(duplicate.id)


async def test_a_duplicate_identity_provider_ref_is_refused_and_not_stored(
    repository: UserRepository,
) -> None:
    original = user()
    await repository.save(original)
    duplicate = user(minutes=1)
    duplicate.identity_provider_ref = original.identity_provider_ref

    with pytest.raises(AlreadyExists) as raised:
        await repository.save(duplicate)

    assert raised.value.field == "identity provider reference"
    with pytest.raises(EntityNotFound):
        await repository.get(duplicate.id)


async def test_a_user_can_be_saved_again_with_its_own_email(repository: UserRepository) -> None:
    original = user()
    await repository.save(original)

    await repository.save(original)

    assert vars(await repository.get(original.id)) == vars(original)
