"""Identifier rules for packages/proto that buf lint cannot express.

Every identifier crosses the wire as a strongly typed id.v1 message, never a bare string, so
passing one entity's ID where another's belongs fails type checking in every generated client.
"""

import re
from collections.abc import Iterator

from google.protobuf.descriptor_pb2 import DescriptorProto, FieldDescriptorProto

ID_PACKAGE = "id.v1"
IDENTIFIER_NAME = re.compile(r"(^|_)(id|uuid|guid|identifier)s?$")
TYPED_ID_NAME = re.compile(r"(^|_)ids?$")
STRING_TYPES = (FieldDescriptorProto.TYPE_STRING, FieldDescriptorProto.TYPE_BYTES)

Messages = list[tuple[str, str, DescriptorProto]]
Located = tuple[str, DescriptorProto, FieldDescriptorProto]


def _fields(messages: Messages) -> Iterator[Located]:
    for package, name, message in messages:
        if package == ID_PACKAGE:
            continue
        for field in message.field:
            yield name, message, field


def _snake(camel: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", camel).lower()


def _camel(snake: str) -> str:
    return "".join(part.title() for part in snake.split("_"))


def _id_field_problem(message: DescriptorProto, field: FieldDescriptorProto) -> str | None:
    """An entity's own ID is `id`; every other ID field is named exactly after its type, with
    no prefix or suffix: `printer_id`, never `assigned_printer_id`."""
    prefix = f".{ID_PACKAGE}."
    id_type = field.type_name.removeprefix(prefix) if field.type_name.startswith(prefix) else None
    if field.name in ("id", "ids"):
        want = f"{message.name}Id"
        return None if id_type == want else f"want type {ID_PACKAGE}.{want}"
    if id_type is None:
        return f"want type {ID_PACKAGE}.{_camel(field.name.removesuffix('s'))}"
    repeated = field.label == FieldDescriptorProto.LABEL_REPEATED
    want_name = _snake(id_type) + ("s" if repeated else "")
    if field.name != want_name:
        return (
            f"type is {ID_PACKAGE}.{id_type}, so name it {want_name} or fix the type;"
            " ID fields take no prefix or suffix"
        )
    return None


def test_no_identifier_is_a_string(messages: Messages) -> None:
    violations = [
        f"{name}.{field.name}"
        for name, _, field in _fields(messages)
        if IDENTIFIER_NAME.search(field.name) and field.type in STRING_TYPES
    ]
    assert not violations, f"Use an id.v1 typed ID instead of a string: {violations}"


def test_id_fields_are_named_exactly_after_their_typed_id(messages: Messages) -> None:
    violations: list[str] = []
    for name, message, field in _fields(messages):
        is_id_field = TYPED_ID_NAME.search(field.name) or field.type_name.startswith(
            f".{ID_PACKAGE}."
        )
        problem = _id_field_problem(message, field) if is_id_field else None
        if problem:
            violations.append(f"{name}.{field.name}: {problem}")
    assert not violations, "\n".join(violations)


def test_id_kernel_holds_only_uuid_wrappers(messages: Messages) -> None:
    uuid_wrapper = [("value", 1, FieldDescriptorProto.TYPE_STRING)]
    violations = [
        name
        for package, name, message in messages
        if package == ID_PACKAGE
        and (
            not message.name.endswith("Id")
            or [(f.name, f.number, f.type) for f in message.field] != uuid_wrapper
        )
    ]
    assert not violations, (
        f"id.v1 messages must be <Entity>Id {{ string value = 1; }}: {violations}"
    )
