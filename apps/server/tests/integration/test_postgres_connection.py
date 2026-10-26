"""Connects to a real Postgres. Skipped unless DB_HOST and the other DB_* variables are set."""

import asyncio
import os

import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from api.common.settings import database_url
from api.infrastructure.postgres_database import PostgresDatabase

pytestmark = pytest.mark.skipif("DB_HOST" not in os.environ, reason="needs Postgres (DB_*)")


def test_health_check_passes_against_postgres() -> None:
    async def check() -> None:
        async with PostgresDatabase(lambda: create_async_engine(database_url())) as database:
            await database.health_check()

    # Async psycopg cannot run on Windows' default ProactorEventLoop.
    asyncio.run(check(), loop_factory=asyncio.SelectorEventLoop)
