"""Made-up values shared between tests, for data the seed in api/infrastructure/dev_data.py does not
hold."""

from datetime import UTC, datetime, timedelta

from core_domain.ids import PrinterQueueId
from core_domain.queue import PrinterQueue

# The fixed time every fake clock reads, so no test depends on the real time.
NOW = datetime(2026, 10, 7, 12, 0, tzinfo=UTC)


def printer_queue(
    is_active: bool, *, minutes: int = 0, printer_queue_id: PrinterQueueId | None = None
) -> PrinterQueue:
    """A queue created minutes after NOW, so tests can order queues by age."""
    created = NOW + timedelta(minutes=minutes)
    queue_id = PrinterQueueId.new() if printer_queue_id is None else printer_queue_id
    return PrinterQueue(queue_id, "Queue", is_active, created, created)
