"""Strongly typed DDD domain ID for the print_preparation domain. Mirrors
id/v1/slice_profile_id.proto."""

from core_domain.ddd.typed_id import TypedId


class SliceProfileId(TypedId):
    __slots__ = ()
