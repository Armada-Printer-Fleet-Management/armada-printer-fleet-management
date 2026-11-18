from collections.abc import Iterator
from uuid import uuid4

import pytest
import sqlalchemy as sa

from api.common.settings import database_url


@pytest.fixture
def engine(monkeypatch: pytest.MonkeyPatch) -> Iterator[sa.Engine]:
    """A throwaway database, dropped after the test, so migrating or downgrading never touches the
    shared one. DB_NAME points at it for the test's duration."""
    name = f"armada_test_{uuid4().hex}"
    # CREATE and DROP DATABASE cannot run inside a transaction.
    admin = sa.create_engine(database_url(), isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.execute(sa.text(f'CREATE DATABASE "{name}"'))
    monkeypatch.setenv("DB_NAME", name)
    test_engine = sa.create_engine(database_url())
    try:
        yield test_engine
    finally:
        test_engine.dispose()
        with admin.connect() as connection:
            connection.execute(sa.text(f'DROP DATABASE "{name}" WITH (FORCE)'))
        admin.dispose()
