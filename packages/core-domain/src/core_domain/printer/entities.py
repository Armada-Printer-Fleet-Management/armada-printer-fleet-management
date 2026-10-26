from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto

from core_domain.ddd import Entity, RuleViolation
from core_domain.ids import PrinterId, PrintJobId


class PrinterStatus(Enum):
    """Mirrors printer.v1.PrinterStatus, without UNSPECIFIED, which is never valid."""

    OFFLINE = auto()
    IDLE = auto()
    PRINTING = auto()
    FINISHED = auto()
    ERROR = auto()


@dataclass(eq=False)
class Printer(Entity[PrinterId]):
    """A physical printer and its latest state reported by the printer server. Shared by every
    app; only the remote server persists a change to one."""

    id: PrinterId
    name: str
    model: str
    status: PrinterStatus
    created_at: datetime
    updated_at: datetime
    print_job_id: PrintJobId | None = None
    progress_percent: int | None = None

    def can_dispatch(self) -> bool:
        return self.status is PrinterStatus.IDLE and self.print_job_id is None

    def dispatch(self, print_job_id: PrintJobId, now: datetime) -> None:
        if not self.can_dispatch():
            raise RuleViolation(f"A {self.status.name} printer cannot take a print job")
        self.status = PrinterStatus.PRINTING
        self.print_job_id = print_job_id
        self.progress_percent = 0
        self.updated_at = now

    def can_release(self) -> bool:
        return self.status in (PrinterStatus.FINISHED, PrinterStatus.ERROR)

    def release(self, now: datetime) -> None:
        if not self.can_release():
            raise RuleViolation(f"A {self.status.name} printer cannot be released")
        self.status = PrinterStatus.IDLE
        self.print_job_id = None
        self.progress_percent = None
        self.updated_at = now
