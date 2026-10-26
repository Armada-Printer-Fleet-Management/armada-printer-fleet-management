from dataclasses import dataclass
from datetime import datetime

from core_domain.ddd import Entity
from core_domain.ids import PrinterQueueId


@dataclass(eq=False)
class PrinterQueue(Entity[PrinterQueueId]):
    """A line of print jobs waiting for a printer. Shared by every app; only the remote server
    persists a change to one."""

    id: PrinterQueueId
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    def can_accept_jobs(self) -> bool:
        return self.is_active
