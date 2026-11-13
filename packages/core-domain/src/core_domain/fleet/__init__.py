"""The fleet domain's entities and rules, shared by every app that handles printers."""

from core_domain.fleet.entities import (
    Printer,
    PrinterCapabilities,
    PrinterStatus,
    PrinterType,
    printer_types,
)

__all__ = ["Printer", "PrinterCapabilities", "PrinterStatus", "PrinterType", "printer_types"]
