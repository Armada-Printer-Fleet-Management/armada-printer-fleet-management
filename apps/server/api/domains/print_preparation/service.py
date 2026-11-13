from collections.abc import Mapping

from core_domain.ddd import Service
from core_domain.ids import SliceProfileId
from core_domain.print_preparation import MachineSpec, SliceProfile, SliceSettings

from api.domains.print_preparation.repository import SliceProfileRepository


class SlicerConfigurationService(Service[SliceProfileRepository]):
    """How the slicer is configured for a print: the slice profiles, and the engine settings
    built from them."""

    async def profile(self, profile_id: SliceProfileId) -> SliceProfile:
        """Raises EntityNotFound for a profile that does not exist."""
        return await self._repository.get(profile_id)

    async def default_profile(self) -> SliceProfile:
        return await self._repository.default()

    async def slice_settings(
        self, machine: MachineSpec, overrides: Mapping[str, str]
    ) -> SliceSettings:
        """The engine settings for slicing on this machine, under the default slice profile.
        Raises RuleViolation for an override the profile does not allow."""
        profile = await self.default_profile()
        return profile.settings_for(machine, overrides)
