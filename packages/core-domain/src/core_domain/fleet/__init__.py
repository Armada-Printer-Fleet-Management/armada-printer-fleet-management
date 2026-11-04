"""The fleet domain's entities and rules, shared by every app that handles printers."""

from core_domain.fleet.entities import Printer, PrinterStatus

__all__ = ["Printer", "PrinterStatus"]
