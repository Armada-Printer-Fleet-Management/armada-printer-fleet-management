from abc import abstractmethod

from core_domain.ddd import AbstractReadRepository
from core_domain.ids import AgreementId, UserId
from core_domain.legal import Agreement, LegalDocument


class AgreementRepository(AbstractReadRepository[AgreementId, Agreement]):
    """This app's user's agreements. The application server keeps them and acceptance is
    requested of it; until the desktop signs in, a local file keeps them instead.
    Implementations live in armada_infrastructure."""

    @abstractmethod
    def outstanding(self, user_id: UserId) -> list[LegalDocument]:
        """The current documents the user has not accepted."""

    @abstractmethod
    def request_accept(self, user_id: UserId, document: LegalDocument) -> Agreement:
        """Raises RuleViolation if this version is no longer the current one."""
