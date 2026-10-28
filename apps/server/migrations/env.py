from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

from api.common.settings import database_url

if context.config.config_file_name is not None:
    fileConfig(context.config.config_file_name)


def run_offline() -> None:
    """Writes the SQL to stdout instead of running it, for `alembic upgrade head --sql`."""
    context.configure(url=database_url(), literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_online() -> None:
    engine = create_engine(database_url())
    with engine.connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_offline()
else:
    run_online()
