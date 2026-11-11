from abc import abstractmethod

from core_domain.ddd import AbstractAsyncRepository
from core_domain.ids import AgreementId, UserId
from core_domain.legal import Agreement


class AgreementRepository(AbstractAsyncRepository[AgreementId, Agreement]):
    """Where the server keeps agreements. Implementations live in api/infrastructure, and each
    must pass tests/contract/test_agreement_repository.py. A user has at most one agreement per
    document version."""

    @abstractmethod
    async def for_user(self, user_id: UserId) -> list[Agreement]:
        """Every agreement the user has made, in no particular order."""

    @abstractmethod
    async def add(self, agreement: Agreement) -> Agreement:
        """Stores a new agreement and returns it. If the user already accepted the same version,
        stores nothing and returns that earlier agreement, so two requests at once cannot record
        it twice."""
