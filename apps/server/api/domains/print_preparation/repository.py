from abc import abstractmethod

from core_domain.ddd import AbstractAsyncReadRepository
from core_domain.ids import SliceProfileId
from core_domain.print_preparation import SliceProfile


class SliceProfileRepository(AbstractAsyncReadRepository[SliceProfileId, SliceProfile]):
    """Where the server reads slice profiles from. Implementations live in api/infrastructure."""

    @abstractmethod
    async def default(self) -> SliceProfile:
        """The profile a slice uses when nothing chooses another."""
