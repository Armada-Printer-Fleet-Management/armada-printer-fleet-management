"""Print jobs, read from and changed on the application server through the print_job domain."""

from core_domain.ids import PrinterId, PrinterQueueId, PrintJobId
from proto_utils.gen.common.v1.page_pb2 import PageResponse
from proto_utils.gen.server.v1.print_job_service_pb2 import (
    GetPrintJobRequest,
    GetPrintJobResponse,
    ListPrintJobsRequest,
    ListPrintJobsResponse,
    TransitionPrintJobRequest,
    TransitionPrintJobResponse,
)
from proto_utils.mappers import PrintJobMapper

from armada_domains.print_job.service import PrintJobService
from armada_ipc._base import IpcModule, proto_call


class PrintJobIpc(IpcModule):
    _mapper = PrintJobMapper()

    def __init__(self, print_jobs: PrintJobService) -> None:
        self._print_jobs = print_jobs

    @proto_call(GetPrintJobRequest)
    def print_job(self, request: GetPrintJobRequest) -> GetPrintJobResponse:
        print_job_id = self._mapper.id_from_proto(PrintJobId, request.print_job_id)
        print_job = self._print_jobs.print_job(print_job_id)
        return GetPrintJobResponse(print_job=self._mapper.to_proto(print_job))

    @proto_call(ListPrintJobsRequest)
    def list_print_jobs(self, request: ListPrintJobsRequest) -> ListPrintJobsResponse:
        """Files are left out; the frontend reads them through the file capability."""
        page = self._print_jobs.page(request.page.page_size, request.page.page_token)
        return ListPrintJobsResponse(
            print_jobs=[self._mapper.to_proto(print_job) for print_job in page.items],
            page=PageResponse(next_page_token=page.next_page_token),
        )

    @proto_call(TransitionPrintJobRequest)
    def transition_print_job(
        self, request: TransitionPrintJobRequest
    ) -> TransitionPrintJobResponse:
        print_job_id = self._mapper.id_from_proto(PrintJobId, request.print_job_id)
        match request.WhichOneof("action"):
            case "start_review":
                print_job = self._print_jobs.start_review(print_job_id)
            case "approve":
                print_job = self._print_jobs.approve(print_job_id)
            case "reject":
                print_job = self._print_jobs.reject(print_job_id, request.reject.reason)
            case "assign":
                printer_id = self._mapper.id_from_proto(PrinterId, request.assign.printer_id)
                print_job = self._print_jobs.assign(print_job_id, printer_id)
            case "move_to_queue":
                printer_queue_id = self._mapper.id_from_proto(
                    PrinterQueueId, request.move_to_queue.printer_queue_id
                )
                print_job = self._print_jobs.move_to_queue(print_job_id, printer_queue_id)
            case "complete":
                print_job = self._print_jobs.complete(print_job_id)
            case "fail":
                print_job = self._print_jobs.fail(print_job_id, request.fail.reason)
            case _:
                raise ValueError("action must be set")
        return TransitionPrintJobResponse(print_job=self._mapper.to_proto(print_job))
