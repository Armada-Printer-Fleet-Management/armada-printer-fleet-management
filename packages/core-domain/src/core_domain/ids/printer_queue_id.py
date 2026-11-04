"""Strongly typed DDD domain ID for the queue domain. Mirrors id/v1/printer_queue_id.proto."""

from core_domain.ddd.typed_id import TypedId


class PrinterQueueId(TypedId):
    __slots__ = ()
