"""What only SqlUserRepository does, beyond the UserRepository contract, while the users table still
predates the entity's names."""

from uuid import uuid4

import pytest
from core_domain.auth import User, UserRole

from api.infrastructure.postgres_database import PostgresDatabase
from api.infrastructure.user_sql import SqlUserRepository
from tests.samples import NOW


@pytest.fixture
def repository(postgres_database: PostgresDatabase) -> SqlUserRepository:
    return SqlUserRepository(postgres_database)


async def test_the_last_name_is_not_stored(repository: SqlUserRepository) -> None:
    user = User.create(
        str(uuid4()), "named@example.com", "First", "Last", UserRole.STUDENT, None, NOW
    )
    await repository.save(user)

    loaded = await repository.get(user.id)

    assert (loaded.first_name, loaded.last_name) == ("First", "")
