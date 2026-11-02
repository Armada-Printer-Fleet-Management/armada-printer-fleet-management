"""File layout rules for packages/proto: the folder is the package, and in a domain package the
file is the entity."""

import re
from pathlib import PurePosixPath

from google.protobuf.descriptor_pb2 import FileDescriptorProto

# The non-domain kinds in packages/proto/AGENTS.md. Every other package is a domain.
NOT_DOMAINS = {"id.v1", "common.v1", "server.v1", "printer_server.v1"}


def _snake(camel: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", camel).lower()


def _entities(proto: FileDescriptorProto) -> list[str]:
    """An entity is a top-level message that carries its own `id`."""
    return [m.name for m in proto.message_type if any(f.name == "id" for f in m.field)]


def _domain_files(proto_files: list[FileDescriptorProto]) -> list[FileDescriptorProto]:
    return [f for f in proto_files if f.package not in NOT_DOMAINS]


def test_package_equals_folder(proto_files: list[FileDescriptorProto]) -> None:
    wrong = [
        f"{f.name} declares {f.package}"
        for f in proto_files
        if f.package != str(PurePosixPath(f.name).parent).replace("/", ".")
    ]
    assert not wrong, wrong


def test_every_entity_has_an_id_file(proto_files: list[FileDescriptorProto]) -> None:
    id_files = {f.name for f in proto_files if f.package == "id.v1"}
    missing = [
        f"{f.name}: {entity} needs id/v1/{_snake(entity)}_id.proto"
        for f in _domain_files(proto_files)
        for entity in _entities(f)
        if f"id/v1/{_snake(entity)}_id.proto" not in id_files
    ]
    assert not missing, missing


def test_entity_file_is_named_after_its_entity(proto_files: list[FileDescriptorProto]) -> None:
    wrong = [
        f"{f.name} holds {entity}; name it {_snake(entity)}.proto"
        for f in _domain_files(proto_files)
        for entity in _entities(f)
        if PurePosixPath(f.name).name != f"{_snake(entity)}.proto"
    ]
    assert not wrong, wrong
