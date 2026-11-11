from abc import abstractmethod

from core_domain.ddd import AbstractReadRepository
from core_domain.ids import AgreementId, UserId
from core_domain.legal import Agreement, LegalDocument


class AgreementRepository(AbstractReadRepository[AgreementId, Agreement]):
    """Agreements as the application server keeps them. Read only; acceptance is requested of
    the server. Implementations live in armada_infrastructure."""

    @abstractmethod
    def outstanding(self, user_id: UserId) -> list[LegalDocument]:
        """The current documents the user has not accepted."""

    @abstractmethod
    def request_accept(self, user_id: UserId, document: LegalDocument) -> Agreement:
        """Raises RuleViolation if the server no longer has this version as current."""
