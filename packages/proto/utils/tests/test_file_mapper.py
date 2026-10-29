from datetime import UTC, datetime

import pytest
from core_domain.file import File, FileType
from core_domain.ids import FileId, UserId

from proto_utils.gen.file.v1 import file_pb2
from proto_utils.mappers import FileMapper

TIME = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)


def every_field_set() -> File:
    return File(
        FileId.new(), UserId.new(), "part.gcode", FileType.CGCODE, 2048, "b" * 64, TIME, TIME
    )


def test_to_proto_maps_every_field_of_the_message() -> None:
    """Fails when a field is added to file.v1.File without being mapped."""
    message = FileMapper().to_proto(every_field_set())
    mapped = {field.name for field, _ in message.ListFields()}
    assert mapped == {field.name for field in file_pb2.File.DESCRIPTOR.fields}


def test_to_entity_reverses_to_proto() -> None:
    file = every_field_set()
    assert vars(FileMapper().to_entity(FileMapper().to_proto(file))) == vars(file)


@pytest.mark.parametrize("file_type", list(FileType))
def test_every_file_type_round_trips(file_type: FileType) -> None:
    file = every_field_set()
    file.file_type = file_type
    assert FileMapper().to_entity(FileMapper().to_proto(file)).file_type is file_type


def test_file_type_from_proto_rejects_unspecified() -> None:
    with pytest.raises(ValueError):
        FileMapper.file_type_from_proto(file_pb2.FILE_TYPE_UNSPECIFIED)
