"""Strongly typed DDD domain ID for the print_job domain. Mirrors id/v1/print_job_id.proto."""

from core_domain.ddd.typed_id import TypedId


class PrintJobId(TypedId):
    __slots__ = ()
