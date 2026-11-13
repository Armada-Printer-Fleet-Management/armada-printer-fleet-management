from core_domain import ids
from core_domain.print_preparation import SettingRange, SliceProfile

from proto_utils.gen.id.v1.slice_profile_id_pb2 import SliceProfileId
from proto_utils.gen.print_preparation.slicing.v1 import slice_profile_pb2
from proto_utils.mapper import ProtoMapper


class SliceProfileMapper(ProtoMapper[SliceProfile, slice_profile_pb2.SliceProfile]):
    def to_proto(self, entity: SliceProfile) -> slice_profile_pb2.SliceProfile:
        return slice_profile_pb2.SliceProfile(
            id=self.id_to_proto(SliceProfileId, entity.id),
            name=entity.name,
            fixed=dict(entity.fixed),
            adjustable={key: _range_to_proto(value) for key, value in entity.adjustable.items()},
        )

    def to_entity(self, message: slice_profile_pb2.SliceProfile) -> SliceProfile:
        return SliceProfile(
            id=self.id_from_proto(ids.SliceProfileId, message.id),
            name=message.name,
            fixed=dict(message.fixed),
            adjustable={key: _range_to_entity(value) for key, value in message.adjustable.items()},
        )


def _range_to_proto(entity: SettingRange) -> slice_profile_pb2.SettingRange:
    return slice_profile_pb2.SettingRange(
        minimum=entity.minimum,
        maximum=entity.maximum,
        choices=sorted(entity.choices or ()),
    )


def _range_to_entity(message: slice_profile_pb2.SettingRange) -> SettingRange:
    return SettingRange(
        minimum=message.minimum if message.HasField("minimum") else None,
        maximum=message.maximum if message.HasField("maximum") else None,
        # An empty list on the wire allows any value, as no choices does.
        choices=frozenset(message.choices) or None,
    )
