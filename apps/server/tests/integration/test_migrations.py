"""Runs the migrations and the dev seed against a real Postgres. Skipped unless DB_HOST and the
other DB_* variables are set. Each run creates its own throwaway database and drops it after, so
it never touches the database the variables name."""

import os
from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

from api.common.settings import database_url
from dev_seed import SEED, seed

pytestmark = pytest.mark.skipif("DB_HOST" not in os.environ, reason="needs Postgres (DB_*)")

ALEMBIC_INI = Path(__file__).parents[2] / "alembic.ini"
# A merged migration is never edited, so the tables this revision creates never change.
REVISION_0001_TABLES = {
    "users",
    "audit_logs",
    "stored_files",
    "printer_queues",
    "printer_queue_tags",
    "printer_queue_memberships",
    "print_jobs",
    "print_job_events",
    "fleet_sections",
    "staff_section_assignments",
    "printers",
    "tags",
    "printer_tags",
    "print_server_instances",
    "printer_events",
    "periods",
    "filament_materials",
    "filament_allocations",
    "filament_ledger_entries",
    "notifications",
    "broadcasts",
    "notification_preferences",
}


@pytest.fixture
def engine(monkeypatch: pytest.MonkeyPatch) -> Iterator[sa.Engine]:
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


def tables(engine: sa.Engine) -> set[str]:
    return set(sa.inspect(engine).get_table_names()) - {"alembic_version"}


def test_revision_0001_creates_the_initial_tables(engine: sa.Engine) -> None:
    command.upgrade(Config(ALEMBIC_INI), "0001")
    assert tables(engine) == REVISION_0001_TABLES


def test_downgrade_from_head_removes_every_table(engine: sa.Engine) -> None:
    config = Config(ALEMBIC_INI)

    command.upgrade(config, "head")
    assert tables(engine)

    command.downgrade(config, "base")
    assert tables(engine) == set()


def test_seed_inserts_each_row_once(engine: sa.Engine) -> None:
    command.upgrade(Config(ALEMBIC_INI), "head")

    assert seed(engine) == sum(len(rows) for _, rows in SEED)
    assert seed(engine) == 0
    with engine.connect() as connection:
        for table, rows in SEED:
            count = connection.execute(sa.select(sa.func.count()).select_from(table)).scalar()
            assert count == len(rows)
