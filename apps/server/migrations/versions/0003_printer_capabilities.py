"""Printer capabilities: what each printer can physically print, one row per printer.

Replaces the printers.capabilities JSON column, which nothing read or wrote. The application server
keeps these values because the printer server cannot always reach every printer.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

_MM_COLUMNS = (
    "build_volume_x_mm",
    "build_volume_y_mm",
    "build_volume_z_mm",
    "nozzle_diameter_mm",
    "filament_diameter_mm",
)


def upgrade() -> None:
    # Printer Fleet (fleet)
    op.create_table(
        "printer_capabilities",
        sa.Column("printer_id", sa.Uuid(), primary_key=True),
        *(sa.Column(name, sa.Numeric(), nullable=False) for name in _MM_COLUMNS),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["printer_id"], ["printers.id"], ondelete="CASCADE"),
    )
    op.drop_column("printers", "capabilities")


def downgrade() -> None:
    op.add_column(
        "printers",
        sa.Column("capabilities", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.drop_table("printer_capabilities")
