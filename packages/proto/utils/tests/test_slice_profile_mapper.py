import pytest
from core_domain.ids import SliceProfileId
from core_domain.print_preparation import MachineSpec, SettingRange, SliceProfile

from proto_utils.gen.fleet.v1 import printer_capabilities_pb2
from proto_utils.gen.print_preparation.slicing.v1 import slice_profile_pb2
from proto_utils.mappers import MachineSpecMapper, SliceProfileMapper


def every_field_set() -> SliceProfile:
    return SliceProfile(
        id=SliceProfileId.new(),
        name="Default",
        fixed={"adhesion_type": "skirt"},
        adjustable={
            "layer_height": SettingRange(minimum=0.1, maximum=0.3),
            "support_enable": SettingRange(choices=frozenset({"true", "false"})),
        },
    )


def test_to_proto_maps_every_field_of_the_message() -> None:
    """Fails when a field is added to print_preparation.slicing.v1.SliceProfile without being
    mapped."""
    message = SliceProfileMapper().to_proto(every_field_set())
    mapped = {field.name for field, _ in message.ListFields()}
    assert mapped == {field.name for field in slice_profile_pb2.SliceProfile.DESCRIPTOR.fields}


def test_to_entity_reverses_to_proto() -> None:
    profile = every_field_set()
    round_tripped = SliceProfileMapper().to_entity(SliceProfileMapper().to_proto(profile))
    assert vars(round_tripped) == vars(profile)


def test_to_entity_rejects_a_profile_without_an_id() -> None:
    message = SliceProfileMapper().to_proto(every_field_set())
    message.ClearField("id")
    with pytest.raises(ValueError):
        SliceProfileMapper().to_entity(message)


def test_machine_spec_round_trips_through_capabilities() -> None:
    machine = MachineSpec(250, 210, 220, 0.4, 1.75)
    capabilities = MachineSpecMapper.to_capabilities(machine)

    assert isinstance(capabilities, printer_capabilities_pb2.PrinterCapabilities)
    assert MachineSpecMapper.from_capabilities(capabilities) == machine
