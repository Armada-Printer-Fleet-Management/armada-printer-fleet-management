from uuid import UUID

import sqlalchemy as sa
from core_domain.ddd import EntityNotFound, Page, TypedId
from core_domain.ids import FileId, PrinterId, PrinterQueueId, PrintJobId, UserId
from core_domain.print_job import PrintJob
from sqlalchemy.dialects.postgresql import insert

from api.domains.print_job.repository import PrintJobRepository
from api.infrastructure.enum_ids import PRINT_JOB_STATUS_IDS
from api.infrastructure.page import decode_token, encode_token, sort_key
from api.infrastructure.sql_repository import SqlRepository

_PRINT_JOB_STATUS = {uuid: status for status, uuid in PRINT_JOB_STATUS_IDS.items()}


_print_jobs = sa.Table(
    "print_jobs",
    sa.MetaData(),
    sa.Column("id", sa.Uuid(), primary_key=True),
    sa.Column("user_id", sa.Uuid(), nullable=False),
    sa.Column("printer_queue_id", sa.Uuid(), nullable=True),
    sa.Column("file_id", sa.Uuid(), nullable=True),
    sa.Column("status", sa.Uuid(), nullable=False),
    sa.Column("status_reason", sa.Text(), nullable=True),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("user_notes", sa.Text(), nullable=False),
    sa.Column("assigned_printer_id", sa.Uuid(), nullable=True),
)


def _uuid(typed_id: TypedId | None) -> UUID | None:
    return None if typed_id is None else typed_id.value


def _typed_id[IdT: TypedId](id_type: type[IdT], value: UUID | None) -> IdT | None:
    return None if value is None else id_type(value)


def _row(print_job: PrintJob) -> dict[str, object]:
    return {
        "id": print_job.id.value,
        "user_id": print_job.user_id.value,
        "printer_queue_id": _uuid(print_job.printer_queue_id),
        "file_id": _uuid(print_job.file_id),
        "status": PRINT_JOB_STATUS_IDS[print_job.status],
        "status_reason": print_job.status_reason,
        "created_at": print_job.created_at,
        "updated_at": print_job.updated_at,
        "user_notes": print_job.user_notes,
        "assigned_printer_id": _uuid(print_job.printer_id),
    }


def _print_job(row: sa.RowMapping) -> PrintJob:
    return PrintJob(
        id=PrintJobId(row["id"]),
        user_id=UserId(row["user_id"]),
        printer_queue_id=_typed_id(PrinterQueueId, row["printer_queue_id"]),
        file_id=_typed_id(FileId, row["file_id"]),
        status=_PRINT_JOB_STATUS[row["status"]],
        status_reason=row["status_reason"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        user_notes=row["user_notes"],
        printer_id=_typed_id(PrinterId, row["assigned_printer_id"]),
    )


class SqlPrintJobRepository(SqlRepository, PrintJobRepository):
    async def get(self, entity_id: PrintJobId) -> PrintJob:
        async with self._transaction() as connection:
            result = await connection.execute(
                sa.select(_print_jobs).where(_print_jobs.c.id == entity_id.value)
            )
            row = result.mappings().one_or_none()
        if row is None:
            raise EntityNotFound(entity_id)
        return _print_job(row)

    async def save(self, entity: PrintJob) -> None:
        row = _row(entity)
        statement = insert(_print_jobs).values(row)
        statement = statement.on_conflict_do_update(
            index_elements=[_print_jobs.c.id],
            set_={column: statement.excluded[column] for column in row if column != "id"},
        )
        async with self._transaction() as connection:
            await connection.execute(statement)

    async def page(self, page_size: int, page_token: str) -> Page[PrintJob]:
        key = _print_jobs.c.created_at, _print_jobs.c.id
        query = sa.select(_print_jobs).order_by(*(column.desc() for column in key))
        if page_token:
            query = query.where(sa.tuple_(*key) < decode_token(page_token))
        # One extra row says whether another page follows, without a COUNT.
        query = query.limit(page_size + 1)
        async with self._transaction() as connection:
            result = await connection.execute(query)
            rows = result.mappings().all()
        items = [_print_job(row) for row in rows[:page_size]]
        more = len(rows) > page_size
        return Page(items, encode_token(sort_key(items[-1])) if more else "")
