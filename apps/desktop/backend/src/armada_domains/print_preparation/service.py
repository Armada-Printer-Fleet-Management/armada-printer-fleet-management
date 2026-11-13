from collections.abc import Mapping

from core_domain.ddd import Service
from core_domain.print_preparation import MachineSpec, SliceSettings

from armada_domains.print_preparation.repository import SlicerConfigurationRepository


class SlicerConfigurationService(Service[SlicerConfigurationRepository]):
    """How the slicer is configured for a print, asked of the application server."""

    def slice_settings(
        self, model: str, machine: MachineSpec, overrides: Mapping[str, str]
    ) -> SliceSettings:
        return self._repository.request_slice_settings(model, machine, overrides)
