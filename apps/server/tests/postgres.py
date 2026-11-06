"""Helpers for tests that use a real Postgres."""

import sqlalchemy as sa


def truncate_tables(engine: sa.Engine) -> None:
    """Empties every table, keeping the migrations in place."""
    with engine.begin() as connection:
        tables = set(sa.inspect(connection).get_table_names()) - {"alembic_version"}
        connection.execute(sa.text(f"TRUNCATE {', '.join(sorted(tables))} CASCADE"))
