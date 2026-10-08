"""Print jobs, read from the application server through the print_job domain."""

from core_domain.ids import PrintJobId
from proto_utils.gen.server.v1.print_job_service_pb2 import GetPrintJobRequest, GetPrintJobResponse
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
