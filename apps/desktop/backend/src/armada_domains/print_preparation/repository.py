from abc import ABC, abstractmethod
from collections.abc import Mapping

from core_domain.print_preparation import MachineSpec, SliceSettings


class SlicerConfigurationRepository(ABC):
    """The slicer configuration as the application server decides it. Settings are requested,
    never built here, so the server's slice profile is the only one applied. Implementations live
    in armada_infrastructure."""

    @abstractmethod
    def request_slice_settings(
        self, model: str, machine: MachineSpec, overrides: Mapping[str, str]
    ) -> SliceSettings:
        """Raises RuleViolation for an override the server's profile does not allow. A printer
        type the fleet does not have is refused by the server with its own error."""
