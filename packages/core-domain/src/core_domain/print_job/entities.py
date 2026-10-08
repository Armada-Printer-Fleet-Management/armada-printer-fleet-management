from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto

from core_domain.ddd import Entity, RuleViolation
from core_domain.ids import FileId, PrinterId, PrintJobId, QueueId, UserId


class PrintJobStatus(Enum):
    """Mirrors print_job.v1.PrintJobStatus, without UNSPECIFIED, which is never valid."""

    DRAFT = auto()
    SUBMITTED = auto()
    UNDER_REVIEW = auto()
    APPROVED = auto()
    REJECTED = auto()
    ASSIGNED = auto()
    PRINTING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


@dataclass(eq=False)
class PrintJob(Entity[PrintJobId]):
    """A request to print one file. Shared by every app; only the remote server persists a change
    to one, so on a client these rules are advisory."""

    id: PrintJobId
    user_id: UserId
    status: PrintJobStatus
    created_at: datetime
    updated_at: datetime
    user_notes: str = ""
    queue_id: QueueId | None = None
    file_id: FileId | None = None
    status_reason: str | None = None
    printer_id: PrinterId | None = None

    def can_start_review(self) -> bool:
        return self.status is PrintJobStatus.SUBMITTED

    def start_review(self, now: datetime) -> None:
        if not self.can_start_review():
            raise RuleViolation(f"A {self.status.name} print job cannot be put under review")
        self.status = PrintJobStatus.UNDER_REVIEW
        self.updated_at = now
