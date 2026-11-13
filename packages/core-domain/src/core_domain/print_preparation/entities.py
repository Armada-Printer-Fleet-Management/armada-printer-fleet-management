from collections.abc import Mapping
from dataclasses import dataclass, field

from core_domain.ddd import Entity, RuleViolation
from core_domain.ids import SliceProfileId

# The engine's command line reads each setting's default and never works out the settings derived
# from others, so every line width is set here as its multiple of the nozzle diameter. Taken from
# the shipped fdmprinter.def.json, where each one's value expression follows the nozzle.
_LINE_WIDTH_NOZZLE_MULTIPLES: Mapping[str, float] = {
    "line_width": 1,
    "wall_line_width": 1,
    "wall_line_width_0": 1,
    "wall_line_width_x": 1,
    "skin_line_width": 1,
    "roofing_line_width": 1,
    "flooring_line_width": 1,
    "infill_line_width": 1,
    "skirt_brim_line_width": 1,
    "support_line_width": 1,
    "support_interface_line_width": 1,
    "support_roof_line_width": 1,
    "support_bottom_line_width": 1,
    "prime_tower_line_width": 1,
    "raft_surface_line_width": 1,
    "min_wall_line_width": 0.85,
    "min_even_wall_line_width": 0.85,
    "min_odd_wall_line_width": 0.85,
    "raft_interface_line_width": 2,
    "raft_base_line_width": 2,
}


@dataclass(frozen=True)
class MachineSpec:
    """What the printer being sliced for can print, in millimetres. A plain value, so this domain
    never depends on the fleet domain's types."""

    width_mm: float
    depth_mm: float
    height_mm: float
    nozzle_diameter_mm: float
    filament_diameter_mm: float


@dataclass(frozen=True)
class SliceSettings:
    """The engine settings for one slice: those for the whole machine, and those for its
    extruder."""

    machine: Mapping[str, str]
    extruder: Mapping[str, str]


@dataclass(frozen=True)
class SettingRange:
    """Limits on a setting a student may change. Unset limits allow any value."""

    minimum: float | None = None
    maximum: float | None = None

    def allows(self, value: str) -> bool:
        if self.minimum is None and self.maximum is None:
            return True
        try:
            number = float(value)
        except ValueError:
            return False
        return (self.minimum is None or number >= self.minimum) and (
            self.maximum is None or number <= self.maximum
        )


@dataclass(eq=False)
class SliceProfile(Entity[SliceProfileId]):
    """What a print may be sliced with: settings the profile always sets, and the only settings a
    student may change, each within its range."""

    id: SliceProfileId
    name: str
    fixed: Mapping[str, str] = field(default_factory=dict[str, str])
    adjustable: Mapping[str, SettingRange] = field(default_factory=dict[str, SettingRange])

    def check_overrides(self, overrides: Mapping[str, str]) -> None:
        """Raises RuleViolation naming the first override this profile does not allow."""
        for key, value in overrides.items():
            allowed = self.adjustable.get(key)
            if allowed is None:
                raise RuleViolation(f"The {key} setting cannot be changed for this print")
            if not allowed.allows(value):
                raise RuleViolation(f"{value} is outside the allowed range for {key}")

    def settings_for(
        self, machine: MachineSpec, overrides: Mapping[str, str] | None = None
    ) -> SliceSettings:
        """The engine settings for slicing on this machine with these overrides. Raises
        RuleViolation for an override the profile does not allow."""
        requested = dict(overrides or {})
        self.check_overrides(requested)
        nozzle = machine.nozzle_diameter_mm
        return SliceSettings(
            machine={
                "machine_width": _number(machine.width_mm),
                "machine_depth": _number(machine.depth_mm),
                "machine_height": _number(machine.height_mm),
                **requested,
                **self.fixed,
            },
            extruder={
                "machine_nozzle_size": _number(nozzle),
                "material_diameter": _number(machine.filament_diameter_mm),
                **{
                    key: _number(round(nozzle * multiple, 4))
                    for key, multiple in _LINE_WIDTH_NOZZLE_MULTIPLES.items()
                },
            },
        )


def _number(value: float) -> str:
    """A setting value as the engine reads it: 250, not 250.0."""
    return format(value, "g")
