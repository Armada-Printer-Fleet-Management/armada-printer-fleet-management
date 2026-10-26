"""The printer domain's entity and rules, shared by every app that handles printers."""

from core_domain.printer.entities import Printer, PrinterStatus

__all__ = ["Printer", "PrinterStatus"]
