from core_domain.print_preparation import SliceSettings

from proto_utils.gen.print_preparation.slicing.v1 import slice_settings_pb2
from proto_utils.mappers import SliceSettingsMapper


def every_field_set() -> SliceSettings:
    return SliceSettings(
        machine={"machine_width": "250", "adhesion_type": "skirt"},
        extruder={"machine_nozzle_size": "0.4", "line_width": "0.4"},
    )


def test_to_proto_maps_every_field_of_the_message() -> None:
    """Fails when a field is added to print_preparation.slicing.v1.SliceSettings without being
    mapped."""
    message = SliceSettingsMapper().to_proto(every_field_set())
    mapped = {field.name for field, _ in message.ListFields()}
    assert mapped == {field.name for field in slice_settings_pb2.SliceSettings.DESCRIPTOR.fields}


def test_to_entity_reverses_to_proto() -> None:
    settings = every_field_set()
    round_tripped = SliceSettingsMapper().to_entity(SliceSettingsMapper().to_proto(settings))
    assert round_tripped == settings
