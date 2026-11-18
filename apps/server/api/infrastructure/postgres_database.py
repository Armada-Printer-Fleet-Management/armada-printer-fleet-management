from collections.abc import Callable, Generator
from contextlib import contextmanager
from types import TracebackType
from typing import Self

import sqlalchemy as sa
from core_domain.ddd import Unavailable
from psycopg.errors import UniqueViolation
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

_DEPENDENCY = "database"


@contextmanager
def database_errors() -> Generator[None]:
    """Turns any failure to reach or use the database into Unavailable."""
    try:
        yield
    except (SQLAlchemyError, OSError) as error:
        raise Unavailable(_DEPENDENCY) from error


def unique_constraint(error: IntegrityError) -> str | None:
    """The name of the unique constraint a write broke, or None when it broke something else."""
    if isinstance(error.orig, UniqueViolation):
        return error.orig.diag.constraint_name
    return None


class PostgresDatabase:
    """The server's connection pool to its Postgres database. Builds the engine when opened, not
    when constructed, so importing the app reads no configuration. Opening does not connect, so
    the server starts while the database is down and the health check reports it."""

    def __init__(self, create_engine: Callable[[], AsyncEngine]) -> None:
        self._create_engine = create_engine
        self._engine: AsyncEngine | None = None

    async def __aenter__(self) -> Self:
        self._engine = self._create_engine()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        engine, self._engine = self._engine, None
        if engine is not None:
            await engine.dispose()

    def engine(self) -> AsyncEngine:
        if self._engine is None:
            raise Unavailable(_DEPENDENCY)
        return self._engine

    async def health_check(self) -> None:
        """Raises Unavailable if the database cannot be reached or is not open."""
        with database_errors():
            async with self.engine().connect() as connection:
                await connection.execute(sa.text("SELECT 1"))
