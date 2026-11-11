from core_domain.ddd import Service
from core_domain.ids import UserId
from core_domain.legal import Agreement, LegalDocument

from armada_domains.legal.repository import AgreementRepository


class AgreementService(Service[AgreementRepository]):
    """The agreements of the one user this app runs for, given by the composition root."""

    def __init__(self, repository: AgreementRepository, user_id: UserId) -> None:
        super().__init__(repository)
        self._user_id = user_id

    def outstanding(self) -> list[LegalDocument]:
        return self._repository.outstanding(self._user_id)

    def accept(self, document: LegalDocument) -> Agreement:
        return self._repository.request_accept(self._user_id, document)
