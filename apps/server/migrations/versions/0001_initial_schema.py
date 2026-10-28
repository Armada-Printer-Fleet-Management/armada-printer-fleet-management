"""Initial schema: every table in the database design, grouped by domain.

Foreign keys exist only inside a domain. An ID that crosses a domain is a plain uuid column, so
one domain never depends on another's tables. Enum columns hold the member's stable UUID from
api/infrastructure/enum_ids.py, never its number or name.
"""

from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def _id() -> sa.Column[UUID]:
    # IDs are chosen by the backend or, for printer events, by the print server, never the database.
    return sa.Column("id", sa.Uuid(), primary_key=True)


def _uuid(name: str, nullable: bool = False) -> sa.Column[UUID]:
    return sa.Column(name, sa.Uuid(), nullable=nullable)


def _enum(name: str, nullable: bool = False) -> sa.Column[UUID]:
    return _uuid(name, nullable)


def _text(name: str, nullable: bool = False) -> sa.Column[str]:
    return sa.Column(name, sa.Text(), nullable=nullable)


def _notes(name: str) -> sa.Column[str]:
    return sa.Column(name, sa.Text(), nullable=False, server_default="")


def _time(name: str, nullable: bool = True) -> sa.Column[datetime]:
    return sa.Column(name, sa.DateTime(timezone=True), nullable=nullable)


def _created_at() -> sa.Column[datetime]:
    return sa.Column(
        "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )


def _updated_at() -> sa.Column[datetime]:
    return sa.Column(
        "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )


def _fk(column: str, target: str, cascade: bool = False) -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(
        [column], [f"{target}.id"], ondelete="CASCADE" if cascade else None
    )


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # Auth / Account
    op.create_table(
        "users",
        _id(),
        _uuid("keycloak_user_id"),
        _text("email"),
        _text("display_name"),
        _enum("role"),
        _enum("status"),
        _time("expires_at"),
        _time("last_login_at"),
        _time("deleted_at"),
        _created_at(),
        _updated_at(),
        sa.UniqueConstraint("keycloak_user_id"),
        sa.UniqueConstraint("email"),
        sa.CheckConstraint("email = lower(email)", name="users_email_lower_case"),
    )
    op.create_table(
        "audit_logs",
        _id(),
        _uuid("actor_user_id", nullable=True),
        _text("actor_client_id", nullable=True),
        _enum("action"),
        _text("target_type"),
        _uuid("target_id"),
        sa.Column("details", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        _created_at(),
        _fk("actor_user_id", "users"),
    )

    # G-code / Model Upload
    op.create_table(
        "stored_files",
        _id(),
        _uuid("owner_user_id"),
        _text("original_filename"),
        _enum("file_type"),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        _text("storage_key"),
        _text("sha256"),
        _enum("upload_status"),
        _enum("scan_status"),
        sa.Column("estimated_print_time_s", sa.Integer(), nullable=True),
        sa.Column("estimated_filament_g", sa.Numeric(), nullable=True),
        _text("material", nullable=True),
        _time("retention_expires_at"),
        _time("deleted_at"),
        _created_at(),
        _updated_at(),
    )
    # Not unique: files with the same content share one stored copy under the same key.
    op.create_index("stored_files_storage_key", "stored_files", ["storage_key"])

    # Queue Management
    op.create_table(
        "printer_queues",
        _id(),
        _text("name"),
        _text("type"),
        _notes("description"),
        _uuid("owner_user_id"),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("max_jobs_per_user", sa.Integer(), nullable=True),
        sa.Column("requires_approval", sa.Boolean(), nullable=False),
        # A pgcrypto crypt() hash. The raw join code is never stored.
        _text("join_code_hash", nullable=True),
        _created_at(),
        _updated_at(),
    )
    op.create_table(
        "printer_queue_tags",
        _uuid("printer_queue_id"),
        _uuid("tag_id"),
        _created_at(),
        _updated_at(),
        sa.PrimaryKeyConstraint("printer_queue_id", "tag_id"),
        _fk("printer_queue_id", "printer_queues", cascade=True),
    )
    op.create_table(
        "printer_queue_memberships",
        _uuid("printer_queue_id"),
        _uuid("user_id"),
        _enum("queue_role"),
        _uuid("added_by"),
        _time("added_at", nullable=False),
        _time("expires_at"),
        _created_at(),
        _updated_at(),
        sa.PrimaryKeyConstraint("printer_queue_id", "user_id"),
        _fk("printer_queue_id", "printer_queues", cascade=True),
    )

    # Job Submission & Dispatch
    op.create_table(
        "print_jobs",
        _id(),
        _uuid("user_id"),
        _uuid("printer_queue_id", nullable=True),
        # Unset while the job is a draft, before its file is uploaded.
        _uuid("file_id", nullable=True),
        _enum("status"),
        # Why the job was rejected, failed or cancelled. Visible to the student.
        _text("status_reason", nullable=True),
        sa.Column("queue_position", sa.Integer(), nullable=True),
        _time("submitted_at"),
        _uuid("approved_by", nullable=True),
        _time("approved_at"),
        _uuid("assigned_printer_id", nullable=True),
        _time("dispatched_at"),
        _time("started_at"),
        _time("completed_at"),
        sa.Column("estimated_filament_g", sa.Numeric(), nullable=True),
        sa.Column("estimated_time_s", sa.Integer(), nullable=True),
        _uuid("material_id", nullable=True),
        _notes("user_notes"),
        _notes("staff_notes"),
        _text("external_job_ref", nullable=True),
        _created_at(),
        _updated_at(),
    )
    op.create_table(
        "print_job_events",
        _id(),
        _uuid("job_id"),
        # Unset on the event that creates the job.
        _enum("from_status", nullable=True),
        _enum("to_status"),
        _uuid("actor_user_id", nullable=True),
        _text("actor_client_id", nullable=True),
        _text("note", nullable=True),
        _created_at(),
        _fk("job_id", "print_jobs"),
    )
    op.create_index(
        "print_job_events_job_id_created_at", "print_job_events", ["job_id", "created_at"]
    )

    # Fleet / Printer Management
    op.create_table(
        "fleet_sections",
        _id(),
        _text("name"),
        _notes("description"),
        _enum("access_policy"),
        _created_at(),
        _updated_at(),
    )
    op.create_table(
        "staff_section_assignments",
        _uuid("user_id"),
        _uuid("section_id"),
        _uuid("granted_by"),
        _time("granted_at", nullable=False),
        _created_at(),
        _updated_at(),
        sa.PrimaryKeyConstraint("user_id", "section_id"),
        _fk("section_id", "fleet_sections", cascade=True),
    )
    op.create_table(
        "print_server_instances",
        _id(),
        _text("name"),
        _text("keycloak_client_id"),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        _created_at(),
        _updated_at(),
        sa.UniqueConstraint("keycloak_client_id"),
    )
    op.create_table(
        "printers",
        _id(),
        _text("name"),
        _uuid("section_id"),
        _text("model"),
        _text("serial_number", nullable=True),
        sa.Column("capabilities", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        _text("external_printer_ref"),
        _uuid("server_instance_id", nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        _notes("notes"),
        _created_at(),
        _updated_at(),
        _fk("section_id", "fleet_sections"),
        _fk("server_instance_id", "print_server_instances"),
    )
    op.create_table(
        "tags",
        _id(),
        _text("name"),
        _created_at(),
        _updated_at(),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "printer_tags",
        _uuid("printer_id"),
        _uuid("tag_id"),
        _created_at(),
        _updated_at(),
        sa.PrimaryKeyConstraint("printer_id", "tag_id"),
        _fk("printer_id", "printers", cascade=True),
        _fk("tag_id", "tags", cascade=True),
    )
    op.create_table(
        "printer_events",
        _id(),
        _uuid("printer_id"),
        _uuid("job_id", nullable=True),
        _enum("event_type"),
        _time("occurred_at", nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=True),
        _enum("failure_reason", nullable=True),
        sa.Column("actual_time_s", sa.Integer(), nullable=True),
        sa.Column("actual_filament_g", sa.Numeric(), nullable=True),
        _uuid("actor_user_id", nullable=True),
        _text("actor_client_id", nullable=True),
        _text("notes", nullable=True),
        _created_at(),
        _fk("printer_id", "printers"),
    )
    op.create_index(
        "printer_events_printer_id_occurred_at", "printer_events", ["printer_id", "occurred_at"]
    )

    # Filament Allocation
    op.create_table(
        "periods",
        _id(),
        _text("name"),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("ends_on", sa.Date(), nullable=False),
        _created_at(),
        _updated_at(),
        sa.CheckConstraint("ends_on >= starts_on", name="periods_ends_after_start"),
    )
    op.create_table(
        "filament_materials",
        _id(),
        _enum("type"),
        _text("brand"),
        _enum("color"),
        sa.Column("cost_per_g", sa.Numeric(), nullable=True),
        sa.Column("is_available", sa.Boolean(), nullable=False),
        _created_at(),
        _updated_at(),
    )
    op.create_table(
        "filament_allocations",
        _id(),
        _uuid("user_id"),
        _uuid("period_id"),
        sa.Column("granted_g", sa.Numeric(), nullable=False),
        _text("source"),
        _time("expires_at"),
        _created_at(),
        _updated_at(),
        _fk("period_id", "periods"),
    )
    op.create_table(
        "filament_ledger_entries",
        _id(),
        _uuid("user_id"),
        _uuid("job_id", nullable=True),
        _enum("entry_type"),
        # Signed: grants and refunds are positive, deductions negative.
        sa.Column("amount_g", sa.Numeric(), nullable=False),
        sa.Column("balance_after_g", sa.Numeric(), nullable=False),
        _text("reason"),
        _uuid("created_by"),
        _created_at(),
    )
    op.create_index(
        "filament_ledger_entries_user_id_created_at",
        "filament_ledger_entries",
        ["user_id", "created_at"],
    )

    # Notifications
    op.create_table(
        "notifications",
        _id(),
        _uuid("recipient_user_id"),
        _enum("type"),
        _enum("channel"),
        _text("subject"),
        _text("body"),
        _uuid("job_id", nullable=True),
        _text("dedupe_key"),
        _enum("status"),
        _time("sent_at"),
        _time("read_at"),
        _created_at(),
        _updated_at(),
        sa.UniqueConstraint("dedupe_key"),
    )
    op.create_table(
        "broadcasts",
        _id(),
        _uuid("sender_user_id"),
        _enum("target_type"),
        _uuid("target_id"),
        _text("subject"),
        _text("body"),
        sa.Column("recipient_count", sa.Integer(), nullable=False),
        _created_at(),
        _updated_at(),
    )
    op.create_table(
        "notification_preferences",
        _uuid("user_id"),
        _enum("type"),
        _enum("channel"),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        _created_at(),
        _updated_at(),
        sa.PrimaryKeyConstraint("user_id", "type", "channel"),
    )


def downgrade() -> None:
    for table in (
        "notification_preferences",
        "broadcasts",
        "notifications",
        "filament_ledger_entries",
        "filament_allocations",
        "filament_materials",
        "periods",
        "printer_events",
        "printer_tags",
        "tags",
        "printers",
        "print_server_instances",
        "staff_section_assignments",
        "fleet_sections",
        "print_job_events",
        "print_jobs",
        "printer_queue_memberships",
        "printer_queue_tags",
        "printer_queues",
        "stored_files",
        "audit_logs",
        "users",
    ):
        op.drop_table(table)
