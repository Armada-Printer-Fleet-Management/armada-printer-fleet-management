"""TimeStatus rules for packages/proto that buf lint cannot express.

A lifecycle need beyond created_at and updated_at, such as soft delete, is a superset message
that nests common.v1.TimeStatus, so a field added to the base reaches every superset.
"""

from google.protobuf.descriptor_pb2 import DescriptorProto

TIME_PACKAGE = "common.v1"

Messages = list[tuple[str, str, DescriptorProto]]


def _is_time_status(package: str, message: DescriptorProto) -> bool:
    return package == TIME_PACKAGE and message.name.endswith("TimeStatus")


def test_time_status_supersets_nest_the_base(messages: Messages) -> None:
    base = f".{TIME_PACKAGE}.TimeStatus"
    violations = [
        name
        for package, name, message in messages
        if _is_time_status(package, message)
        and message.name != "TimeStatus"
        and base not in [field.type_name for field in message.field]
    ]
    assert not violations, f"A TimeStatus superset must nest common.v1.TimeStatus: {violations}"
