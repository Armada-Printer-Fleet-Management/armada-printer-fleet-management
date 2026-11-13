import pytest

from core_domain.ddd import RuleViolation
from core_domain.ids import SliceProfileId
from core_domain.print_preparation import SettingRange, SliceProfile

TOGGLE = SettingRange(choices=frozenset({"true", "false"}))


def test_a_choice_is_allowed_and_any_other_value_refused() -> None:
    assert TOGGLE.allows("true")
    assert not TOGGLE.allows("yes")


def test_choices_and_limits_must_both_hold() -> None:
    layer_height = SettingRange(minimum=0.1, maximum=0.3, choices=frozenset({"0.1", "0.2", "0.4"}))

    assert layer_height.allows("0.2")
    assert not layer_height.allows("0.15")  # within the limits, not a choice
    assert not layer_height.allows("0.4")  # a choice, outside the limits


def test_a_profile_refuses_a_value_outside_a_settings_choices() -> None:
    profile = SliceProfile(SliceProfileId.new(), "Default", adjustable={"support_enable": TOGGLE})

    with pytest.raises(RuleViolation):
        profile.check_overrides({"support_enable": "maybe"})
