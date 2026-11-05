"""Helpers for tests that use a real Postgres."""

import asyncio
from collections.abc import Coroutine

import sqlalchemy as sa


def run[T](coroutine: Coroutine[object, object, T]) -> T:
    # Async psycopg cannot run on Windows' default ProactorEventLoop.
    return asyncio.run(coroutine, loop_factory=asyncio.SelectorEventLoop)


def truncate_tables(engine: sa.Engine) -> None:
    """Empties every table, keeping the migrations in place."""
    with engine.begin() as connection:
        tables = set(sa.inspect(connection).get_table_names()) - {"alembic_version"}
        connection.execute(sa.text(f"TRUNCATE {', '.join(sorted(tables))} CASCADE"))
