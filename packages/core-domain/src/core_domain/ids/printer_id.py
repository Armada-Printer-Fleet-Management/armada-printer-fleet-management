"""Strongly typed DDD domain ID for the fleet domain. Mirrors id/v1/printer_id.proto."""

from core_domain.ddd.typed_id import TypedId


class PrinterId(TypedId):
    __slots__ = ()
