from collections.abc import Mapping

from core_domain.ddd import Service
from core_domain.print_preparation import MachineSpec, SliceProfile, SliceSettings

from api.domains.print_preparation.repository import SliceProfileRepository


class SlicerConfigurationService(Service[SliceProfileRepository]):
    """How the slicer is configured for a print: the slice profiles, and the engine settings
    built from them."""

    async def default_profile(self) -> SliceProfile:
        return await self._repository.default()

    async def slice_settings(
        self, machine: MachineSpec, overrides: Mapping[str, str]
    ) -> SliceSettings:
        """The engine settings for slicing on this machine, under the default slice profile.
        Raises RuleViolation for an override the profile does not allow."""
        profile = await self.default_profile()
        return profile.settings_for(machine, overrides)
