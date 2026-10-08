"""Strongly typed DDD domain ID for the file domain. Mirrors id/v1/file_id.proto."""

from core_domain.ddd.typed_id import TypedId


class FileId(TypedId):
    __slots__ = ()
