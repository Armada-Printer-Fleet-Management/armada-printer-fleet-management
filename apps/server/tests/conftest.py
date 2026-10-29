from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from api.common.settings import database_url
from api.infrastructure.postgres_database import PostgresDatabase
from tests.postgres import run

ALEMBIC_INI = Path(__file__).parents[1] / "alembic.ini"


@pytest.fixture(scope="session")
def migrated_database_url() -> Iterator[str]:
    """A throwaway database migrated to head, created once per run and dropped after, so tests
    never touch the database the DB_* variables name."""
    name = f"armada_test_{uuid4().hex}"
    # CREATE and DROP DATABASE cannot run inside a transaction.
    admin = sa.create_engine(database_url(), isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.execute(sa.text(f'CREATE DATABASE "{name}"'))
    try:
        # The migrations read DB_NAME, so it points at the throwaway database only while they run.
        with pytest.MonkeyPatch.context() as monkeypatch:
            monkeypatch.setenv("DB_NAME", name)
            url = database_url()
            command.upgrade(Config(ALEMBIC_INI), "head")
        yield url
    finally:
        with admin.connect() as connection:
            connection.execute(sa.text(f'DROP DATABASE "{name}" WITH (FORCE)'))
        admin.dispose()


@pytest.fixture
def postgres_database(migrated_database_url: str) -> Iterator[PostgresDatabase]:
    """An open PostgresDatabase over the throwaway database, with every table emptied first."""
    engine = sa.create_engine(migrated_database_url)
    with engine.begin() as connection:
        tables = set(sa.inspect(connection).get_table_names()) - {"alembic_version"}
        connection.execute(sa.text(f"TRUNCATE {', '.join(sorted(tables))} CASCADE"))
    engine.dispose()

    # NullPool, because each run() is a new event loop and a pooled connection belongs to the
    # loop that opened it.
    database = PostgresDatabase(
        lambda: create_async_engine(migrated_database_url, poolclass=NullPool)
    )
    run(database.__aenter__())
    try:
        yield database
    finally:
        run(database.__aexit__(None, None, None))
