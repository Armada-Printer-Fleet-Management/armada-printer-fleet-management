"""Conversions between typed IDs and the uuid columns the SQL repositories store them in."""

from uuid import UUID

from core_domain.ddd import TypedId


def optional_uuid(typed_id: TypedId | None) -> UUID | None:
    return None if typed_id is None else typed_id.value


def optional_typed_id[IdT: TypedId](id_type: type[IdT], value: UUID | None) -> IdT | None:
    return None if value is None else id_type(value)
