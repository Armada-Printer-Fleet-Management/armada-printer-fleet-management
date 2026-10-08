from connectrpc.code import Code
from connectrpc.errors import ConnectError
from connectrpc.request import RequestContext
from core_domain.ids import PrintJobId
from proto_utils.gen.server.v1.print_job_service_pb2 import (
    CreatePrintJobRequest,
    CreatePrintJobResponse,
    CreatePrintJobUploadRequest,
    CreatePrintJobUploadResponse,
    GetPrintJobRequest,
    GetPrintJobResponse,
    ListPrintJobsRequest,
    ListPrintJobsResponse,
    SubmitPrintJobRequest,
    SubmitPrintJobResponse,
    TransitionPrintJobRequest,
    TransitionPrintJobResponse,
)
from proto_utils.mappers import PrintJobMapper

from api.domains.print_job.service import PrintJobService
from api.services.domain_errors import domain_errors_as_connect, request_id


class PrintJobServiceImplementation:
    """The Connect handler for server.v1.PrintJobService. It only translates between the wire and
    the print_job domain: rules live on the entity, use cases on the domain service."""

    _mapper = PrintJobMapper()

    def __init__(self, print_jobs: PrintJobService) -> None:
        self._print_jobs = print_jobs

    async def get_print_job(
        self,
        request: GetPrintJobRequest,
        ctx: RequestContext[GetPrintJobRequest, GetPrintJobResponse],
        /,
    ) -> GetPrintJobResponse:
        print_job_id = request_id(PrintJobId, request.print_job_id)
        with domain_errors_as_connect():
            print_job = await self._print_jobs.print_job(print_job_id)
        return GetPrintJobResponse(print_job=self._mapper.to_proto(print_job))

    async def transition_print_job(
        self,
        request: TransitionPrintJobRequest,
        ctx: RequestContext[TransitionPrintJobRequest, TransitionPrintJobResponse],
        /,
    ) -> TransitionPrintJobResponse:
        print_job_id = request_id(PrintJobId, request.print_job_id)
        action = request.WhichOneof("action")
        if action is None:
            raise ConnectError(Code.INVALID_ARGUMENT, "action must be set")
        if action != "start_review":
            raise ConnectError(Code.UNIMPLEMENTED, f"{action} is not implemented yet")
        with domain_errors_as_connect():
            print_job = await self._print_jobs.start_review(print_job_id)
        return TransitionPrintJobResponse(print_job=self._mapper.to_proto(print_job))

    async def create_print_job(
        self,
        request: CreatePrintJobRequest,
        ctx: RequestContext[CreatePrintJobRequest, CreatePrintJobResponse],
        /,
    ) -> CreatePrintJobResponse:
        raise ConnectError(Code.UNIMPLEMENTED, "CreatePrintJob is not implemented yet")

    async def create_print_job_upload(
        self,
        request: CreatePrintJobUploadRequest,
        ctx: RequestContext[CreatePrintJobUploadRequest, CreatePrintJobUploadResponse],
        /,
    ) -> CreatePrintJobUploadResponse:
        raise ConnectError(Code.UNIMPLEMENTED, "CreatePrintJobUpload is not implemented yet")

    async def submit_print_job(
        self,
        request: SubmitPrintJobRequest,
        ctx: RequestContext[SubmitPrintJobRequest, SubmitPrintJobResponse],
        /,
    ) -> SubmitPrintJobResponse:
        raise ConnectError(Code.UNIMPLEMENTED, "SubmitPrintJob is not implemented yet")

    async def list_print_jobs(
        self,
        request: ListPrintJobsRequest,
        ctx: RequestContext[ListPrintJobsRequest, ListPrintJobsResponse],
        /,
    ) -> ListPrintJobsResponse:
        raise ConnectError(Code.UNIMPLEMENTED, "ListPrintJobs is not implemented yet")
