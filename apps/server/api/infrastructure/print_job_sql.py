import sqlalchemy as sa
from core_domain.ddd import EntityNotFound, Page
from core_domain.ids import FileId, PrinterId, PrinterQueueId, PrintJobId, UserId
from core_domain.print_job import PrintJob

from api.domains.print_job.repository import PrintJobRepository
from api.infrastructure.enum_ids import PRINT_JOB_STATUS_IDS, by_stored_id
from api.infrastructure.sql_columns import optional_typed_id, optional_uuid
from api.infrastructure.sql_repository import SqlRepository

_PRINT_JOB_STATUS = by_stored_id(PRINT_JOB_STATUS_IDS)


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
    sa.Column("printer_id", sa.Uuid(), nullable=True),
)


def _row(print_job: PrintJob) -> dict[str, object]:
    return {
        "id": print_job.id.value,
        "user_id": print_job.user_id.value,
        "printer_queue_id": optional_uuid(print_job.printer_queue_id),
        "file_id": optional_uuid(print_job.file_id),
        "status": PRINT_JOB_STATUS_IDS[print_job.status],
        "status_reason": print_job.status_reason,
        "created_at": print_job.created_at,
        "updated_at": print_job.updated_at,
        "user_notes": print_job.user_notes,
        "printer_id": optional_uuid(print_job.printer_id),
    }


def _print_job(row: sa.RowMapping) -> PrintJob:
    return PrintJob(
        id=PrintJobId(row["id"]),
        user_id=UserId(row["user_id"]),
        printer_queue_id=optional_typed_id(PrinterQueueId, row["printer_queue_id"]),
        file_id=optional_typed_id(FileId, row["file_id"]),
        status=_PRINT_JOB_STATUS[row["status"]],
        status_reason=row["status_reason"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        user_notes=row["user_notes"],
        printer_id=optional_typed_id(PrinterId, row["printer_id"]),
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
        await self._upsert(_print_jobs, _row(entity))

    async def page(self, page_size: int, page_token: str) -> Page[PrintJob]:
        return await self._newest_first_page(_print_jobs, _print_job, page_size, page_token)
