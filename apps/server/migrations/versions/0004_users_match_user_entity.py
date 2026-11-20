"""Users match the User entity: every column has the entity field's name and type.

- users.display_name becomes first_name, which is what it already held, and last_name is added.
  Existing rows get an empty last name.
- users.keycloak_user_ref becomes identity_provider_ref, stored as text, since not every identity
  provider uses UUIDs. Its unique constraint is renamed with it.
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Auth (auth)
    op.alter_column("users", "display_name", new_column_name="first_name")
    # The default fills existing rows, then goes, so a new row must always say its last name.
    op.add_column("users", sa.Column("last_name", sa.Text(), nullable=False, server_default=""))
    op.alter_column("users", "last_name", server_default=None)

    op.alter_column(
        "users",
        "keycloak_user_ref",
        new_column_name="identity_provider_ref",
        type_=sa.Text(),
        postgresql_using="keycloak_user_ref::text",
    )
    op.execute(
        "ALTER TABLE users RENAME CONSTRAINT users_keycloak_user_ref_key"
        " TO users_identity_provider_ref_key"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE users RENAME CONSTRAINT users_identity_provider_ref_key"
        " TO users_keycloak_user_ref_key"
    )
    # Fails if a provider's reference is not a UUID: such a row cannot go back to the old schema.
    op.alter_column(
        "users",
        "identity_provider_ref",
        new_column_name="keycloak_user_ref",
        type_=sa.Uuid(),
        postgresql_using="identity_provider_ref::uuid",
    )

    op.drop_column("users", "last_name")
    op.alter_column("users", "first_name", new_column_name="display_name")
