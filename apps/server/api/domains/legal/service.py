from collections.abc import Callable, Iterable
from datetime import datetime

from core_domain.ddd import Service
from core_domain.ids import AgreementId, UserId
from core_domain.legal import Agreement, LegalDocument, outstanding

from api.domains.legal.repository import AgreementRepository


class AgreementService(Service[AgreementRepository]):
    def __init__(
        self,
        repository: AgreementRepository,
        documents: Iterable[LegalDocument],
        clock: Callable[[], datetime],
    ) -> None:
        super().__init__(repository)
        self._documents = list(documents)
        self._clock = clock

    async def agreement(self, agreement_id: AgreementId) -> Agreement:
        return await self._repository.get(agreement_id)

    def documents(self) -> list[LegalDocument]:
        """The current version of every legal document, as this build ships them."""
        return list(self._documents)

    async def outstanding(self, user_id: UserId) -> list[LegalDocument]:
        """The current documents the user has not accepted, which they must accept before
        using the software."""
        return outstanding(self._documents, await self._repository.for_user(user_id))

    async def accept(self, user_id: UserId, document: LegalDocument) -> Agreement:
        """Records that the user accepted the document. Raises RuleViolation if it is not the
        current version. Accepting a version again returns the first agreement."""
        agreement = Agreement.accept(user_id, document, self._documents, self._clock())
        return await self._repository.add(agreement)
