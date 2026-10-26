from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncConnection

from api.infrastructure.postgres_database import PostgresDatabase, database_errors


class SqlRepository:
    """Base for the adapters that implement a domain's repository port over the database."""

    def __init__(self, database: PostgresDatabase) -> None:
        self._database = database

    @asynccontextmanager
    async def _transaction(self) -> AsyncGenerator[AsyncConnection]:
        """A connection inside one transaction: committed if the block finishes, rolled back if
        it raises. Database failures become Unavailable."""
        with database_errors():
            async with self._database.engine().begin() as connection:
                yield connection
