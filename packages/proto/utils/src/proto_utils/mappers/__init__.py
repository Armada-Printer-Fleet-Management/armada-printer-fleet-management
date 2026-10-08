"""One mapper per core-domain entity, converting it to and from its wire message (its DTO).
DTOs need not match entities field for field: internal entity state stays off the wire, and a
caller-specific view is shaped by the caller."""

from proto_utils.mappers.print_job import PrintJobMapper

__all__ = ["PrintJobMapper"]
