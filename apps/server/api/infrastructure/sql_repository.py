from collections.abc import AsyncGenerator, Callable, Collection, Mapping
from contextlib import asynccontextmanager

import sqlalchemy as sa
from core_domain.ddd import AlreadyExists, Page
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection

from api.infrastructure.page import Keyed, decode_token, encode_token, sort_key
from api.infrastructure.postgres_database import (
    PostgresDatabase,
    database_errors,
    unique_constraint,
)

# A unique constraint's name, and the entity and field AlreadyExists reports for it.
type UniqueFields = Mapping[str, tuple[str, str]]


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

    async def _upsert(
        self,
        table: sa.Table,
        row: Mapping[str, object],
        insert_only: Collection[str] = (),
        unique: UniqueFields | None = None,
    ) -> None:
        """Inserts the row, or overwrites an existing row with the same id. Columns in
        insert_only keep the value they were inserted with. Breaking a constraint named in unique
        raises AlreadyExists and stores nothing."""
        statement = insert(table).values(row)
        statement = statement.on_conflict_do_update(
            index_elements=[table.c.id],
            set_={
                column: statement.excluded[column]
                for column in row
                if column != "id" and column not in insert_only
            },
        )
        async with self._transaction() as connection:
            try:
                await connection.execute(statement)
            except IntegrityError as error:
                duplicate = (unique or {}).get(unique_constraint(error) or "")
                if duplicate is None:
                    raise
                raise AlreadyExists(*duplicate) from error

    async def _newest_first_page[EntityT: Keyed](
        self,
        table: sa.Table,
        entity: Callable[[sa.RowMapping], EntityT],
        page_size: int,
        page_token: str,
    ) -> Page[EntityT]:
        """A page of the table's rows, newest first by (created_at, id)."""
        key = table.c.created_at, table.c.id
        query = sa.select(table).order_by(*(column.desc() for column in key))
        if page_token:
            query = query.where(sa.tuple_(*key) < decode_token(page_token))
        # One extra row says whether another page follows, without a COUNT.
        query = query.limit(page_size + 1)
        async with self._transaction() as connection:
            result = await connection.execute(query)
            rows = result.mappings().all()
        items = [entity(row) for row in rows[:page_size]]
        more = len(rows) > page_size
        return Page(items, encode_token(sort_key(items[-1])) if more else "")
