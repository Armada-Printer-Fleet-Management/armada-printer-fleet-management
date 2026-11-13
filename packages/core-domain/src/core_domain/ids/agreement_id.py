"""Strongly typed DDD domain ID for the legal domain. Mirrors id/v1/agreement_id.proto."""

from core_domain.ddd.typed_id import TypedId


class AgreementId(TypedId):
    __slots__ = ()
