from core_domain.print_preparation import SliceSettings

from proto_utils.gen.print_preparation.slicing.v1 import slice_settings_pb2
from proto_utils.mapper import ProtoMapper


class SliceSettingsMapper(ProtoMapper[SliceSettings, slice_settings_pb2.SliceSettings]):
    def to_proto(self, entity: SliceSettings) -> slice_settings_pb2.SliceSettings:
        return slice_settings_pb2.SliceSettings(
            machine_settings=dict(entity.machine), extruder_settings=dict(entity.extruder)
        )

    def to_entity(self, message: slice_settings_pb2.SliceSettings) -> SliceSettings:
        return SliceSettings(
            machine=dict(message.machine_settings), extruder=dict(message.extruder_settings)
        )
