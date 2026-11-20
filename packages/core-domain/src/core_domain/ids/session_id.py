"""Strongly typed DDD domain ID for the auth domain. Mirrors id/v1/session_id.proto."""

from core_domain.ddd.typed_id import TypedId


class SessionId(TypedId):
    __slots__ = ()
