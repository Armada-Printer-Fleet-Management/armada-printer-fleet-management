from core_domain.ddd import Page
from core_domain.ids import PrinterId, PrinterQueueId, PrintJobId
from core_domain.print_job import PrintJob
from proto_utils.gen.common.v1.page_pb2 import PageRequest
from proto_utils.gen.id.v1 import print_job_id_pb2, printer_id_pb2, printer_queue_id_pb2
from proto_utils.gen.server.v1.print_job_service_connect import PrintJobServiceClientSync
from proto_utils.gen.server.v1.print_job_service_pb2 import (
    GetPrintJobRequest,
    ListPrintJobsRequest,
    TransitionPrintJobRequest,
)
from proto_utils.mappers import PrintJobMapper

from armada_domains.print_job.repository import PrintJobRepository
from armada_infrastructure.application_server.client import ApplicationServerClient
from armada_infrastructure.application_server.connection import ApplicationServerConnection


class ApplicationServerPrintJobs(
    ApplicationServerClient[PrintJobId, print_job_id_pb2.PrintJobId], PrintJobRepository
):
    """Reads print jobs from the application server, which owns them, and asks it for changes."""

    _id_message_type = print_job_id_pb2.PrintJobId
    _mapper = PrintJobMapper()

    def __init__(self, server: ApplicationServerConnection) -> None:
        self._client = PrintJobServiceClientSync(server.address, http_client=server.http_client)

    def get(self, entity_id: PrintJobId) -> PrintJob:
        request = GetPrintJobRequest(print_job_id=self._id(entity_id))
        with self._server_errors_as_domain(entity_id):
            response = self._client.get_print_job(request)
        return self._mapper.to_entity(response.print_job)

    def page(self, page_size: int, page_token: str) -> Page[PrintJob]:
        request = ListPrintJobsRequest(page=PageRequest(page_size=page_size, page_token=page_token))
        with self._server_errors_as_domain():
            response = self._client.list_print_jobs(request)
        return Page(
            [self._mapper.to_entity(print_job) for print_job in response.print_jobs],
            response.page.next_page_token,
        )

    def _transition(self, request: TransitionPrintJobRequest) -> PrintJob:
        print_job_id = self._mapper.id_from_proto(PrintJobId, request.print_job_id)
        with self._server_errors_as_domain(print_job_id):
            response = self._client.transition_print_job(request)
        return self._mapper.to_entity(response.print_job)

    def request_start_review(self, print_job_id: PrintJobId) -> PrintJob:
        return self._transition(
            TransitionPrintJobRequest(
                print_job_id=self._id(print_job_id),
                start_review=TransitionPrintJobRequest.StartReview(),
            )
        )

    def request_approve(self, print_job_id: PrintJobId) -> PrintJob:
        return self._transition(
            TransitionPrintJobRequest(
                print_job_id=self._id(print_job_id), approve=TransitionPrintJobRequest.Approve()
            )
        )

    def request_reject(self, print_job_id: PrintJobId, reason: str) -> PrintJob:
        return self._transition(
            TransitionPrintJobRequest(
                print_job_id=self._id(print_job_id),
                reject=TransitionPrintJobRequest.Reject(reason=reason),
            )
        )

    def request_assign(self, print_job_id: PrintJobId, printer_id: PrinterId) -> PrintJob:
        printer = self._mapper.id_to_proto(printer_id_pb2.PrinterId, printer_id)
        return self._transition(
            TransitionPrintJobRequest(
                print_job_id=self._id(print_job_id),
                assign=TransitionPrintJobRequest.Assign(printer_id=printer),
            )
        )

    def request_move_to_queue(
        self, print_job_id: PrintJobId, printer_queue_id: PrinterQueueId
    ) -> PrintJob:
        queue = self._mapper.id_to_proto(printer_queue_id_pb2.PrinterQueueId, printer_queue_id)
        return self._transition(
            TransitionPrintJobRequest(
                print_job_id=self._id(print_job_id),
                move_to_queue=TransitionPrintJobRequest.MoveToQueue(printer_queue_id=queue),
            )
        )

    def request_complete(self, print_job_id: PrintJobId) -> PrintJob:
        return self._transition(
            TransitionPrintJobRequest(
                print_job_id=self._id(print_job_id), complete=TransitionPrintJobRequest.Complete()
            )
        )

    def request_fail(self, print_job_id: PrintJobId, reason: str) -> PrintJob:
        return self._transition(
            TransitionPrintJobRequest(
                print_job_id=self._id(print_job_id),
                fail=TransitionPrintJobRequest.Fail(reason=reason),
            )
        )
