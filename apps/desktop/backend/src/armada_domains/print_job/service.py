from core_domain.ddd import Service
from core_domain.ids import PrintJobId
from core_domain.print_job import PrintJob

from armada_domains.print_job.repository import PrintJobRepository


class PrintJobService(Service[PrintJobRepository]):
    def print_job(self, print_job_id: PrintJobId) -> PrintJob:
        return self._repository.get(print_job_id)
