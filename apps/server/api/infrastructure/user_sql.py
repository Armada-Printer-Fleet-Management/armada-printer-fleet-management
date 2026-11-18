from uuid import UUID

import sqlalchemy as sa
from core_domain.auth import User
from core_domain.ddd import EntityNotFound, Page
from core_domain.ids import UserId

from api.domains.auth.repository import UserRepository
from api.infrastructure.enum_ids import USER_ROLE_IDS, USER_STATUS_IDS, by_stored_id
from api.infrastructure.sql_repository import SqlRepository, UniqueFields

_USER_ROLE = by_stored_id(USER_ROLE_IDS)
_USER_STATUS = by_stored_id(USER_STATUS_IDS)
# Postgres's default names for the table's unique constraints.
_UNIQUE: UniqueFields = {
    "users_email_key": ("user", "email"),
    "users_keycloak_user_ref_key": ("user", "identity provider subject"),
}


_users = sa.Table(
    "users",
    sa.MetaData(),
    sa.Column("id", sa.Uuid(), primary_key=True),
    sa.Column("keycloak_user_ref", sa.Uuid(), nullable=False),
    sa.Column("email", sa.Text(), nullable=False),
    sa.Column("display_name", sa.Text(), nullable=False),
    sa.Column("role", sa.Uuid(), nullable=False),
    sa.Column("status", sa.Uuid(), nullable=False),
    sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
)


# The schema predates the entity's names, so until it is migrated the first name is stored as
# display_name, the last name is not stored, and the subject must be a UUID.
def _row(user: User) -> dict[str, object]:
    return {
        "id": user.id.value,
        "keycloak_user_ref": UUID(user.identity_provider_subject),
        "email": user.email,
        "display_name": user.first_name,
        "role": USER_ROLE_IDS[user.role],
        "status": USER_STATUS_IDS[user.status],
        "expires_at": user.expires_at,
        "last_login_at": user.last_login_at,
        "deleted_at": user.deleted_at,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }


def _user(row: sa.RowMapping) -> User:
    return User(
        id=UserId(row["id"]),
        identity_provider_subject=str(row["keycloak_user_ref"]),
        email=row["email"],
        first_name=row["display_name"],
        last_name="",
        role=_USER_ROLE[row["role"]],
        status=_USER_STATUS[row["status"]],
        expires_at=row["expires_at"],
        last_login_at=row["last_login_at"],
        deleted_at=row["deleted_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class SqlUserRepository(SqlRepository, UserRepository):
    async def get(self, entity_id: UserId) -> User:
        async with self._transaction() as connection:
            result = await connection.execute(
                sa.select(_users).where(_users.c.id == entity_id.value)
            )
            row = result.mappings().one_or_none()
        if row is None:
            raise EntityNotFound(entity_id)
        return _user(row)

    async def save(self, entity: User) -> None:
        await self._upsert(_users, _row(entity), unique=_UNIQUE)

    async def page(self, page_size: int, page_token: str) -> Page[User]:
        return await self._newest_first_page(_users, _user, page_size, page_token)
