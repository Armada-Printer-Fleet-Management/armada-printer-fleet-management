from core_domain.ddd import Page, Service
from core_domain.ids import PrinterId, PrinterQueueId, PrintJobId
from core_domain.print_job import PrintJob

from armada_domains.print_job.repository import PrintJobRepository


class PrintJobService(Service[PrintJobRepository]):
    def print_job(self, print_job_id: PrintJobId) -> PrintJob:
        return self._repository.get(print_job_id)

    def page(self, page_size: int, page_token: str) -> Page[PrintJob]:
        return self._repository.page(page_size, page_token)

    def start_review(self, print_job_id: PrintJobId) -> PrintJob:
        return self._repository.request_start_review(print_job_id)

    def approve(self, print_job_id: PrintJobId) -> PrintJob:
        return self._repository.request_approve(print_job_id)

    def reject(self, print_job_id: PrintJobId, reason: str) -> PrintJob:
        return self._repository.request_reject(print_job_id, reason)

    def assign(self, print_job_id: PrintJobId, printer_id: PrinterId) -> PrintJob:
        return self._repository.request_assign(print_job_id, printer_id)

    def move_to_queue(self, print_job_id: PrintJobId, printer_queue_id: PrinterQueueId) -> PrintJob:
        return self._repository.request_move_to_queue(print_job_id, printer_queue_id)

    def complete(self, print_job_id: PrintJobId) -> PrintJob:
        return self._repository.request_complete(print_job_id)

    def fail(self, print_job_id: PrintJobId, reason: str) -> PrintJob:
        return self._repository.request_fail(print_job_id, reason)
