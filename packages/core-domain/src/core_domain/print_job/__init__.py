"""The print_job domain's entity and rules, shared by every app that handles print jobs."""

from core_domain.print_job.entities import PrintJob, PrintJobStatus

__all__ = ["PrintJob", "PrintJobStatus"]
