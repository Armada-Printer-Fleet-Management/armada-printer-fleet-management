"""Brings the database up to this image's newest migration, for the deploy stack's migrate service.

A database at a revision this image does not know was migrated by a newer version. It is left as
it is rather than failing, because armada's schema epoch has already decided whether this version
may run against it.
"""

import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from alembic.util import CommandError
from sqlalchemy import create_engine

from api.common.settings import database_url

ALEMBIC_INI = Path(__file__).parent / "alembic.ini"


def unknown_revisions(config: Config) -> list[str]:
    """The database's current revisions that this image's migrations do not include."""
    script = ScriptDirectory.from_config(config)
    engine = create_engine(database_url())
    try:
        with engine.connect() as connection:
            heads = MigrationContext.configure(connection).get_current_heads()
    finally:
        engine.dispose()
    unknown: list[str] = []
    for head in heads:
        try:
            script.get_revision(head)
        except CommandError:
            unknown.append(head)
    return unknown


def main() -> None:
    config = Config(ALEMBIC_INI)
    unknown = unknown_revisions(config)
    if unknown:
        print(
            f"migrate: the database is at {', '.join(unknown)}, newer than this version's "
            "migrations; leaving it as it is",
            file=sys.stderr,
        )
        return
    command.upgrade(config, "head")


if __name__ == "__main__":
    main()
