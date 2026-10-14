from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Self

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

    @classmethod
    def create(cls, user_id: UserId, user_notes: str, now: datetime) -> Self:
        return cls(PrintJobId.new(), user_id, PrintJobStatus.DRAFT, now, now, user_notes)

    def can_attach_file(self) -> bool:
        return self.status is PrintJobStatus.DRAFT

    def require_can_attach_file(self) -> None:
        if not self.can_attach_file():
            raise RuleViolation(f"A {self.status.name} print job cannot have its file changed")

    def attach_file(self, file_id: FileId, now: datetime) -> None:
        self.require_can_attach_file()
        self.file_id = file_id
        self.updated_at = now

    def can_submit(self, file_uploaded: bool) -> bool:
        return self.status is PrintJobStatus.DRAFT and self.file_id is not None and file_uploaded

    def submit(self, file_uploaded: bool, now: datetime) -> None:
        if self.status is not PrintJobStatus.DRAFT:
            raise RuleViolation(f"A {self.status.name} print job cannot be submitted")
        if not self.can_submit(file_uploaded):
            raise RuleViolation("A print job cannot be submitted until its file is uploaded")
        self.status = PrintJobStatus.SUBMITTED
        self.updated_at = now

    def can_start_review(self) -> bool:
        return self.status is PrintJobStatus.SUBMITTED

    def start_review(self, now: datetime) -> None:
        if not self.can_start_review():
            raise RuleViolation(f"A {self.status.name} print job cannot be put under review")
        self.status = PrintJobStatus.UNDER_REVIEW
        self.updated_at = now

    def can_approve(self) -> bool:
        return self.status is PrintJobStatus.UNDER_REVIEW

    def approve(self, now: datetime) -> None:
        if not self.can_approve():
            raise RuleViolation(f"A {self.status.name} print job cannot be approved")
        self.status = PrintJobStatus.APPROVED
        self.updated_at = now

    def can_reject(self) -> bool:
        return self.status is PrintJobStatus.UNDER_REVIEW

    def reject(self, reason: str, now: datetime) -> None:
        if not self.can_reject():
            raise RuleViolation(f"A {self.status.name} print job cannot be rejected")
        if not reason.strip():
            raise RuleViolation("A print job cannot be rejected without a reason")
        self.status = PrintJobStatus.REJECTED
        self.status_reason = reason
        self.updated_at = now

    def can_assign(self) -> bool:
        return self.status is PrintJobStatus.APPROVED

    def assign(self, printer_id: PrinterId, now: datetime) -> None:
        if not self.can_assign():
            raise RuleViolation(f"A {self.status.name} print job cannot be assigned")
        self.status = PrintJobStatus.ASSIGNED
        self.printer_id = printer_id
        self.updated_at = now
