"""Runs migrate.py, the deploy stack's migration entry point, against a real Postgres."""

from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

import migrate

ALEMBIC_INI = Path(__file__).parents[3] / "alembic.ini"
# Made up, and past any revision the migrations will reach, as a newer version would leave it.
NEWER_REVISION = "9999"


def revision(engine: sa.Engine) -> str | None:
    with engine.connect() as connection:
        return connection.execute(sa.text("SELECT version_num FROM alembic_version")).scalar()


def test_a_database_at_head_stays_at_head(engine: sa.Engine) -> None:
    config = Config(ALEMBIC_INI)
    command.upgrade(config, "head")

    migrate.main()

    assert revision(engine) == ScriptDirectory.from_config(config).get_current_head()


def test_a_database_ahead_of_this_version_is_left_as_it_is(engine: sa.Engine) -> None:
    command.upgrade(Config(ALEMBIC_INI), "head")
    with engine.begin() as connection:
        connection.execute(
            sa.text("UPDATE alembic_version SET version_num = :newer"), {"newer": NEWER_REVISION}
        )

    migrate.main()

    assert revision(engine) == NEWER_REVISION
