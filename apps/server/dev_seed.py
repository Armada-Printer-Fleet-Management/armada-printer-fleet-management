# Writes the development data in api/infrastructure/dev_data.py into the development database.
# Run after the migrations by the dev stack's migrate service; never by a deployment. Rows that
# already exist are left alone, so it is safe to rerun.
"""Seed the development database. Reads the DB_* environment variables."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert

from api.common.settings import database_url
from api.infrastructure.dev_data import (
    STUB_FLEET_SECTION_ID,
    STUB_STAFF_ID,
    STUB_STUDENT_ID,
    stub_files,
    stub_fleet_sections,
    stub_print_jobs,
    stub_printer_queues,
    stub_printers,
    stub_users,
)
from api.infrastructure.enum_ids import (
    FILE_SCAN_STATUS_CLEAN_ID,
    FILE_TYPE_IDS,
    FILE_UPLOAD_STATUS_UPLOADED_ID,
    FLEET_ACCESS_POLICY_STAFF_ONLY_ID,
    PRINT_JOB_STATUS_IDS,
    USER_ROLE_IDS,
    USER_STATUS_ACTIVE_ID,
)

Rows = list[dict[str, object]]


def _table(name: str, *columns: str) -> sa.TableClause:
    clauses: list[sa.ColumnClause[object]] = [sa.column(column) for column in columns]
    return sa.table(name, *clauses)


_users = _table("users", "id", "keycloak_user_id", "email", "display_name", "role", "status")
_fleet_sections = _table("fleet_sections", "id", "name", "access_policy")
_printer_queues = _table(
    "printer_queues", "id", "name", "type", "owner_user_id", "is_active", "requires_approval"
)
_printers = _table(
    "printers", "id", "name", "section_id", "model", "external_printer_ref", "is_enabled"
)
_stored_files = _table(
    "stored_files",
    "id",
    "owner_user_id",
    "original_filename",
    "file_type",
    "size_bytes",
    "storage_key",
    "sha256",
    "upload_status",
    "scan_status",
    "created_at",
    "updated_at",
)
_print_jobs = _table(
    "print_jobs",
    "id",
    "user_id",
    "printer_queue_id",
    "file_id",
    "status",
    "status_reason",
    "assigned_printer_id",
    "user_notes",
    "created_at",
    "updated_at",
)


def _user_rows() -> Rows:
    return [
        {
            "id": user.id.value,
            "keycloak_user_id": user.keycloak_user_id,
            "email": user.email,
            "display_name": user.display_name,
            "role": USER_ROLE_IDS[user.role],
            "status": USER_STATUS_ACTIVE_ID,
        }
        for user in stub_users()
    ]


def _fleet_section_rows() -> Rows:
    return [
        {"id": section.id, "name": section.name, "access_policy": FLEET_ACCESS_POLICY_STAFF_ONLY_ID}
        for section in stub_fleet_sections()
    ]


def _printer_queue_rows() -> Rows:
    return [
        {
            "id": queue.id.value,
            "name": queue.name,
            "type": "general",
            "owner_user_id": STUB_STAFF_ID.value,
            "is_active": queue.is_active,
            "requires_approval": True,
        }
        for queue in stub_printer_queues()
    ]


def _printer_rows() -> Rows:
    # A printer's status, current job and progress are reported by the printer server, not stored.
    return [
        {
            "id": printer.id.value,
            "name": printer.name,
            "section_id": STUB_FLEET_SECTION_ID,
            "model": printer.model,
            "external_printer_ref": str(printer.id.value),
            "is_enabled": True,
        }
        for printer in stub_printers()
    ]


def _stored_file_rows() -> Rows:
    return [
        {
            "id": file.id.value,
            "owner_user_id": STUB_STUDENT_ID.value,
            "original_filename": file.filename,
            "file_type": FILE_TYPE_IDS[file.file_type],
            "size_bytes": file.size_bytes,
            "storage_key": file.storage_key(),
            "sha256": file.sha256,
            "upload_status": FILE_UPLOAD_STATUS_UPLOADED_ID,
            "scan_status": FILE_SCAN_STATUS_CLEAN_ID,
            "created_at": file.created_at,
            "updated_at": file.updated_at,
        }
        for file in stub_files()
    ]


def _print_job_rows() -> Rows:
    return [
        {
            "id": job.id.value,
            "user_id": job.user_id.value,
            "printer_queue_id": job.printer_queue_id.value if job.printer_queue_id else None,
            "file_id": job.file_id.value if job.file_id else None,
            "status": PRINT_JOB_STATUS_IDS[job.status],
            "status_reason": job.status_reason,
            "assigned_printer_id": job.printer_id.value if job.printer_id else None,
            "user_notes": job.user_notes,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
        }
        for job in stub_print_jobs()
    ]


# Parents before the rows that refer to them.
SEED: list[tuple[sa.TableClause, Rows]] = [
    (_users, _user_rows()),
    (_fleet_sections, _fleet_section_rows()),
    (_printer_queues, _printer_queue_rows()),
    (_printers, _printer_rows()),
    (_stored_files, _stored_file_rows()),
    (_print_jobs, _print_job_rows()),
]


def seed(engine: sa.Engine) -> int:
    """Inserts every seed row that is missing and returns how many were inserted."""
    inserted = 0
    with engine.begin() as connection:
        for table, rows in SEED:
            # Counted from RETURNING, since a multi-row insert's rowcount is not reliable.
            statement = insert(table).values(rows).on_conflict_do_nothing().returning(table.c.id)
            inserted += len(connection.execute(statement).all())
    return inserted


if __name__ == "__main__":
    engine = sa.create_engine(database_url())
    print(f"dev seed: inserted {seed(engine)} rows")
    engine.dispose()
