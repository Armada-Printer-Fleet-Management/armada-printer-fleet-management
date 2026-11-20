"""One mapper per core-domain entity, converting it to and from its wire message (its DTO).
DTOs need not match entities field for field: internal entity state stays off the wire, and a
caller-specific view is shaped by the caller."""

from proto_utils.mappers.agreement import AgreementMapper
from proto_utils.mappers.file import FileMapper
from proto_utils.mappers.machine_spec import MachineSpecMapper
from proto_utils.mappers.print_job import PrintJobMapper
from proto_utils.mappers.printer import PrinterMapper, PrinterTypeMapper
from proto_utils.mappers.printer_queue import PrinterQueueMapper
from proto_utils.mappers.session import SessionMapper
from proto_utils.mappers.slice_profile import SliceProfileMapper
from proto_utils.mappers.slice_settings import SliceSettingsMapper
from proto_utils.mappers.user import UserMapper

__all__ = [
    "AgreementMapper",
    "FileMapper",
    "MachineSpecMapper",
    "PrintJobMapper",
    "PrinterMapper",
    "PrinterQueueMapper",
    "PrinterTypeMapper",
    "SessionMapper",
    "SliceProfileMapper",
    "SliceSettingsMapper",
    "UserMapper",
]
