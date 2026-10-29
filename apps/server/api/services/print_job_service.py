from collections.abc import Callable

import structlog
from connectrpc.code import Code
from connectrpc.errors import ConnectError
from connectrpc.request import RequestContext
from core_domain.file import File
from core_domain.ids import FileId, PrinterId, PrinterQueueId, PrintJobId, UserId
from core_domain.print_job import PrintJob
from proto_utils.gen.common.v1.page_pb2 import PageResponse
from proto_utils.gen.file.v1.file_upload_pb2 import FileUploadSlot
from proto_utils.gen.id.v1.file_id_pb2 import FileId as FileIdMessage
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
from proto_utils.mappers import FileMapper, PrintJobMapper

from api.domains.file.service import FileService
from api.domains.print_job.service import PrintJobService
from api.domains.printer.service import PrinterService
from api.domains.printer_queue.service import PrinterQueueService
from api.routers.file import upload_path
from api.services.domain_errors import domain_errors_as_connect, request_id
from api.services.request_url import absolute_url

logger = structlog.stdlib.get_logger(__name__)


class PrintJobServiceImplementation:
    """The Connect handler for server.v1.PrintJobService. It translates between the wire and the
    print_job domain, and composes it with the file, printer and printer_queue domains where an
    RPC involves them: rules live on the entities, use cases on the domain services."""

    _mapper = PrintJobMapper()
    _file_mapper = FileMapper()

    def __init__(
        self,
        print_jobs: PrintJobService,
        files: FileService,
        printers: PrinterService,
        printer_queues: PrinterQueueService,
        caller: Callable[[], UserId],
    ) -> None:
        self._print_jobs = print_jobs
        self._files = files
        self._printers = printers
        self._printer_queues = printer_queues
        self._caller = caller

    async def _file_of(self, print_job: PrintJob) -> File | None:
        if print_job.file_id is None:
            return None
        files = await self._files.files([print_job.file_id])
        if not files:
            # The job still exists, so it is returned without its file rather than reported missing.
            logger.warning(
                "print job file record is missing",
                print_job_id=str(print_job.id),
                file_id=str(print_job.file_id),
            )
            return None
        return files[0]

    async def get_print_job(
        self,
        request: GetPrintJobRequest,
        ctx: RequestContext[GetPrintJobRequest, GetPrintJobResponse],
        /,
    ) -> GetPrintJobResponse:
        print_job_id = request_id(PrintJobId, request.print_job_id)
        with domain_errors_as_connect():
            print_job = await self._print_jobs.print_job(print_job_id)
            file = await self._file_of(print_job)
        return GetPrintJobResponse(
            print_job=self._mapper.to_proto(print_job),
            file=None if file is None else self._file_mapper.to_proto(file),
        )

    async def transition_print_job(
        self,
        request: TransitionPrintJobRequest,
        ctx: RequestContext[TransitionPrintJobRequest, TransitionPrintJobResponse],
        /,
    ) -> TransitionPrintJobResponse:
        print_job_id = request_id(PrintJobId, request.print_job_id)
        with domain_errors_as_connect():
            match request.WhichOneof("action"):
                case "start_review":
                    print_job = await self._print_jobs.start_review(print_job_id)
                case "approve":
                    print_job = await self._print_jobs.approve(print_job_id)
                case "reject":
                    print_job = await self._print_jobs.reject(print_job_id, request.reject.reason)
                case "assign":
                    printer_id = request_id(PrinterId, request.assign.printer_id)

                    async def dispatch() -> bool:
                        printer = await self._printers.dispatch(printer_id, print_job_id)
                        return printer.print_job_id == print_job_id

                    print_job = await self._print_jobs.assign(print_job_id, printer_id, dispatch)
                case "move_to_queue":
                    printer_queue_id = request_id(
                        PrinterQueueId, request.move_to_queue.printer_queue_id
                    )
                    await self._printer_queues.get(printer_queue_id)
                    print_job = await self._print_jobs.move_to_queue(print_job_id, printer_queue_id)
                case "complete":
                    print_job = await self._print_jobs.complete(print_job_id)
                case "fail":
                    print_job = await self._print_jobs.fail(print_job_id, request.fail.reason)
                case _:
                    raise ConnectError(Code.INVALID_ARGUMENT, "action must be set")
        return TransitionPrintJobResponse(print_job=self._mapper.to_proto(print_job))

    async def create_print_job(
        self,
        request: CreatePrintJobRequest,
        ctx: RequestContext[CreatePrintJobRequest, CreatePrintJobResponse],
        /,
    ) -> CreatePrintJobResponse:
        with domain_errors_as_connect():
            print_job = await self._print_jobs.create(self._caller(), request.user_notes)
        return CreatePrintJobResponse(print_job=self._mapper.to_proto(print_job))

    async def create_print_job_upload(
        self,
        request: CreatePrintJobUploadRequest,
        ctx: RequestContext[CreatePrintJobUploadRequest, CreatePrintJobUploadResponse],
        /,
    ) -> CreatePrintJobUploadResponse:
        print_job_id = request_id(PrintJobId, request.print_job_id)
        metadata = request.metadata
        try:
            file_type = FileMapper.file_type_from_proto(metadata.file_type)
        except ValueError as error:
            raise ConnectError(Code.INVALID_ARGUMENT, "metadata.file_type must be set") from error

        created: list[File] = []

        async def new_file() -> FileId:
            created.append(
                await self._files.create_upload(
                    self._caller(),
                    metadata.filename,
                    file_type,
                    metadata.size_bytes,
                    metadata.sha256,
                )
            )
            return created[0].id

        with domain_errors_as_connect():
            await self._print_jobs.attach_new_file(print_job_id, new_file)
        file = created[0]
        slot = FileUploadSlot(
            file_id=FileMapper.id_to_proto(FileIdMessage, file.id),
            upload_url=absolute_url(ctx, upload_path(file.id)),
        )
        return CreatePrintJobUploadResponse(slot=slot)

    async def submit_print_job(
        self,
        request: SubmitPrintJobRequest,
        ctx: RequestContext[SubmitPrintJobRequest, SubmitPrintJobResponse],
        /,
    ) -> SubmitPrintJobResponse:
        print_job_id = request_id(PrintJobId, request.print_job_id)
        with domain_errors_as_connect():
            printer_queue_id = await self._printer_queues.open_queue()
            print_job = await self._print_jobs.submit(
                print_job_id, self._files.is_uploaded, printer_queue_id
            )
            file = await self._file_of(print_job)
        return SubmitPrintJobResponse(
            print_job=self._mapper.to_proto(print_job),
            file=None if file is None else self._file_mapper.to_proto(file),
        )

    async def list_print_jobs(
        self,
        request: ListPrintJobsRequest,
        ctx: RequestContext[ListPrintJobsRequest, ListPrintJobsResponse],
        /,
    ) -> ListPrintJobsResponse:
        with domain_errors_as_connect():
            page = await self._print_jobs.page(request.page.page_size, request.page.page_token)
            files = await self._files.files(
                print_job.file_id for print_job in page.items if print_job.file_id is not None
            )
        return ListPrintJobsResponse(
            print_jobs=[self._mapper.to_proto(print_job) for print_job in page.items],
            files=[self._file_mapper.to_proto(file) for file in files],
            page=PageResponse(next_page_token=page.next_page_token),
        )
