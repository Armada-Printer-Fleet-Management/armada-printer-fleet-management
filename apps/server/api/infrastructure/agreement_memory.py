# Keeps agreements in process memory, for tests that need an AgreementRepository without Postgres.
# The server uses SqlAgreementRepository; both pass tests/contract/test_agreement_repository.py.
from collections.abc import Iterable
from dataclasses import replace

from core_domain.ddd import EntityNotFound
from core_domain.ids import AgreementId, UserId
from core_domain.legal import Agreement

from api.domains.legal.repository import AgreementRepository


class InMemoryAgreementRepository(AgreementRepository):
    def __init__(self, agreements: Iterable[Agreement] = ()) -> None:
        self._agreements = {agreement.id: agreement for agreement in agreements}

    async def get(self, entity_id: AgreementId) -> Agreement:
        if entity_id not in self._agreements:
            raise EntityNotFound(entity_id)
        return replace(self._agreements[entity_id])

    async def for_user(self, user_id: UserId) -> list[Agreement]:
        return [replace(a) for a in self._agreements.values() if a.user_id == user_id]

    async def save(self, entity: Agreement) -> None:
        self._agreements[entity.id] = replace(entity)

    async def add(self, agreement: Agreement) -> Agreement:
        for existing in self._agreements.values():
            same_version = (existing.user_id, existing.kind, existing.effective_date) == (
                agreement.user_id,
                agreement.kind,
                agreement.effective_date,
            )
            if same_version:
                return replace(existing)
        await self.save(agreement)
        return replace(agreement)
