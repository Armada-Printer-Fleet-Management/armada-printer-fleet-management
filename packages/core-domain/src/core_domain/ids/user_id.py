"""Strongly typed DDD domain ID for the user domain. Mirrors id/v1/user_id.proto."""

from core_domain.ddd.typed_id import TypedId


class UserId(TypedId):
    __slots__ = ()
