import sqlalchemy as sa
from core_domain.ddd import EntityNotFound
from core_domain.ids import AgreementId, UserId
from core_domain.legal import Agreement
from sqlalchemy.dialects.postgresql import insert

from api.domains.legal.repository import AgreementRepository
from api.infrastructure.enum_ids import LEGAL_DOCUMENT_KIND_IDS, by_stored_id
from api.infrastructure.sql_repository import SqlRepository

_KIND = by_stored_id(LEGAL_DOCUMENT_KIND_IDS)

_agreements = sa.Table(
    "agreements",
    sa.MetaData(),
    sa.Column("id", sa.Uuid(), primary_key=True),
    sa.Column("user_id", sa.Uuid(), nullable=False),
    sa.Column("kind", sa.Uuid(), nullable=False),
    sa.Column("effective_date", sa.Date(), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
)
_VERSION = ("user_id", "kind", "effective_date")


def _row(agreement: Agreement) -> dict[str, object]:
    return {
        "id": agreement.id.value,
        "user_id": agreement.user_id.value,
        "kind": LEGAL_DOCUMENT_KIND_IDS[agreement.kind],
        "effective_date": agreement.effective_date,
        "created_at": agreement.created_at,
        "updated_at": agreement.updated_at,
    }


def _agreement(row: sa.RowMapping) -> Agreement:
    return Agreement(
        id=AgreementId(row["id"]),
        user_id=UserId(row["user_id"]),
        kind=_KIND[row["kind"]],
        effective_date=row["effective_date"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class SqlAgreementRepository(SqlRepository, AgreementRepository):
    async def get(self, entity_id: AgreementId) -> Agreement:
        async with self._transaction() as connection:
            result = await connection.execute(
                sa.select(_agreements).where(_agreements.c.id == entity_id.value)
            )
            row = result.mappings().one_or_none()
        if row is None:
            raise EntityNotFound(entity_id)
        return _agreement(row)

    async def for_user(self, user_id: UserId) -> list[Agreement]:
        async with self._transaction() as connection:
            result = await connection.execute(
                sa.select(_agreements).where(_agreements.c.user_id == user_id.value)
            )
            rows = result.mappings().all()
        return [_agreement(row) for row in rows]

    async def save(self, entity: Agreement) -> None:
        row = _row(entity)
        statement = insert(_agreements).values(row)
        statement = statement.on_conflict_do_update(
            index_elements=[_agreements.c.id],
            set_={column: statement.excluded[column] for column in row if column != "id"},
        )
        async with self._transaction() as connection:
            await connection.execute(statement)

    async def add(self, agreement: Agreement) -> Agreement:
        row = _row(agreement)
        version = [_agreements.c[column] == row[column] for column in _VERSION]
        statement = insert(_agreements).values(row).on_conflict_do_nothing(index_elements=_VERSION)
        async with self._transaction() as connection:
            await connection.execute(statement)
            result = await connection.execute(sa.select(_agreements).where(*version))
            return _agreement(result.mappings().one())
