"""StringValue stands in for an id.v1 message: both are a message with one `string value`."""

from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest
from google.protobuf.wrappers_pb2 import StringValue

from proto_utils import ProtoMapper


@dataclass(frozen=True)
class ThingId:
    value: UUID


@dataclass
class Thing:
    id: ThingId


class ThingMapper(ProtoMapper[Thing, StringValue]):
    def to_proto(self, entity: Thing) -> StringValue:
        return self.id_to_proto(StringValue, entity.id)

    def to_entity(self, message: StringValue) -> Thing:
        return Thing(self.id_from_proto(ThingId, message))


def test_a_mapper_round_trips_its_entity() -> None:
    thing = Thing(ThingId(uuid4()))
    assert ThingMapper().to_entity(ThingMapper().to_proto(thing)) == thing


def test_a_mapper_must_implement_both_directions() -> None:
    class Half(ProtoMapper[Thing, StringValue]):
        def to_proto(self, entity: Thing) -> StringValue:
            return StringValue()

    with pytest.raises(TypeError):
        Half()  # type: ignore[abstract] -- the point of the test: it cannot be built


def test_id_from_proto_rejects_a_value_that_is_not_a_uuid() -> None:
    with pytest.raises(ValueError):
        ProtoMapper.id_from_proto(ThingId, StringValue(value="not-a-uuid"))
    with pytest.raises(ValueError):
        ProtoMapper.id_from_proto(ThingId, StringValue())


def test_optional_ids_map_unset_to_none_and_back() -> None:
    assert ProtoMapper.optional_id_from_proto(ThingId, StringValue()) is None
    assert ProtoMapper.optional_id_to_proto(StringValue, None) is None
    value = uuid4()
    message = ProtoMapper.optional_id_to_proto(StringValue, ThingId(value))
    assert message is not None
    assert ProtoMapper.optional_id_from_proto(ThingId, message) == ThingId(value)
