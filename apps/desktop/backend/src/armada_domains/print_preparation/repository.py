from abc import abstractmethod
from collections.abc import Mapping

from core_domain.ddd import AbstractReadRepository
from core_domain.ids import SliceProfileId
from core_domain.print_preparation import MachineSpec, SliceProfile, SliceSettings


class SlicerConfigurationRepository(AbstractReadRepository[SliceProfileId, SliceProfile]):
    """The slice profiles as the application server keeps them. Settings are requested, never
    built here, so the server's slice profile is the only one applied. Implementations live in
    armada_infrastructure."""

    @abstractmethod
    def request_slice_settings(
        self, model: str, machine: MachineSpec, overrides: Mapping[str, str]
    ) -> SliceSettings:
        """Raises RuleViolation for an override the server's profile does not allow. A printer
        type the fleet does not have is refused by the server with its own error."""
