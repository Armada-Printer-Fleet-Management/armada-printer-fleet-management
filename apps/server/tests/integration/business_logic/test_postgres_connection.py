"""Connects to a real Postgres."""

from sqlalchemy.ext.asyncio import create_async_engine

from api.common.settings import database_url
from api.infrastructure.postgres_database import PostgresDatabase


async def test_health_check_passes_against_postgres() -> None:
    async with PostgresDatabase(lambda: create_async_engine(database_url())) as database:
        await database.health_check()
