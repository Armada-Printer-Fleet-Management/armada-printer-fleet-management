from collections.abc import Iterable

import sqlalchemy as sa
from core_domain.content_asset import File
from core_domain.ddd import EntityNotFound
from core_domain.ids import FileId, UserId
from sqlalchemy.dialects.postgresql import insert

from api.domains.content_asset.repository import FileRepository
from api.infrastructure.enum_ids import (
    FILE_SCAN_STATUS_NOT_SCANNED_ID,
    FILE_TYPE_IDS,
    by_stored_id,
)
from api.infrastructure.sql_repository import SqlRepository

_FILE_TYPE = by_stored_id(FILE_TYPE_IDS)
# Written on insert only, so a later save never resets a status something else has set.
_INSERT_ONLY = {"scan_status"}


_files = sa.Table(
    "files",
    sa.MetaData(),
    sa.Column("id", sa.Uuid(), primary_key=True),
    sa.Column("user_id", sa.Uuid(), nullable=False),
    sa.Column("filename", sa.Text(), nullable=False),
    sa.Column("file_type", sa.Uuid(), nullable=False),
    sa.Column("size_bytes", sa.BigInteger(), nullable=False),
    sa.Column("storage_key", sa.Text(), nullable=False),
    sa.Column("sha256", sa.Text(), nullable=False),
    sa.Column("scan_status", sa.Uuid(), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
)


def _row(file: File) -> dict[str, object]:
    return {
        "id": file.id.value,
        "user_id": file.user_id.value,
        "filename": file.filename,
        "file_type": FILE_TYPE_IDS[file.file_type],
        "size_bytes": file.size_bytes,
        "storage_key": file.storage_key(),
        "sha256": file.sha256,
        # The column is required, but nothing tracks scan state yet.
        "scan_status": FILE_SCAN_STATUS_NOT_SCANNED_ID,
        "created_at": file.created_at,
        "updated_at": file.updated_at,
    }


def _file(row: sa.RowMapping) -> File:
    return File(
        id=FileId(row["id"]),
        user_id=UserId(row["user_id"]),
        filename=row["filename"],
        file_type=_FILE_TYPE[row["file_type"]],
        size_bytes=row["size_bytes"],
        sha256=row["sha256"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class SqlFileRepository(SqlRepository, FileRepository):
    async def get(self, entity_id: FileId) -> File:
        async with self._transaction() as connection:
            result = await connection.execute(
                sa.select(_files).where(_files.c.id == entity_id.value)
            )
            row = result.mappings().one_or_none()
        if row is None:
            raise EntityNotFound(entity_id)
        return _file(row)

    async def get_many(self, file_ids: Iterable[FileId]) -> list[File]:
        values = [file_id.value for file_id in file_ids]
        if not values:
            return []
        async with self._transaction() as connection:
            result = await connection.execute(sa.select(_files).where(_files.c.id.in_(values)))
            rows = result.mappings().all()
        return [_file(row) for row in rows]

    async def save(self, entity: File) -> None:
        row = _row(entity)
        statement = insert(_files).values(row)
        statement = statement.on_conflict_do_update(
            index_elements=[_files.c.id],
            set_={
                column: statement.excluded[column]
                for column in row
                if column != "id" and column not in _INSERT_ONLY
            },
        )
        async with self._transaction() as connection:
            await connection.execute(statement)

    async def delete(self, file_id: FileId) -> None:
        async with self._transaction() as connection:
            result = await connection.execute(sa.delete(_files).where(_files.c.id == file_id.value))
        if result.rowcount == 0:
            raise EntityNotFound(file_id)

    async def is_storage_key_used(self, storage_key: str) -> bool:
        async with self._transaction() as connection:
            result = await connection.execute(
                sa.select(sa.exists().where(_files.c.storage_key == storage_key))
            )
            return result.scalar_one()
