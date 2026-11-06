import pytest
import sqlalchemy as sa

from api.infrastructure.postgres_database import PostgresDatabase
from tests.postgres import truncate_tables


@pytest.fixture
def empty_database(
    postgres_database: PostgresDatabase, database_engine: sa.Engine
) -> PostgresDatabase:
    """The stack's database with the seed removed, so a SQL adapter starts as empty as every other
    adapter under the same contract."""
    truncate_tables(database_engine)
    return postgres_database
