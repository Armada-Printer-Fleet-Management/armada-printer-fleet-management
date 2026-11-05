import pytest
import sqlalchemy as sa

from api.common.settings import database_url
from api.infrastructure.postgres_database import PostgresDatabase
from tests.postgres import truncate_tables


@pytest.fixture
def empty_database(postgres_database: PostgresDatabase) -> PostgresDatabase:
    """The stack's database with the seed removed, so a SQL adapter starts as empty as every other
    adapter under the same contract."""
    engine = sa.create_engine(database_url())
    try:
        truncate_tables(engine)
    finally:
        engine.dispose()
    return postgres_database
