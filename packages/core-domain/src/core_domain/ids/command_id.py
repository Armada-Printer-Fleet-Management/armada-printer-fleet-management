"""Strongly typed DDD domain ID for idempotent commands. Mirrors id/v1/command_id.proto."""

from core_domain.ddd.typed_id import TypedId


class CommandId(TypedId):
    __slots__ = ()
