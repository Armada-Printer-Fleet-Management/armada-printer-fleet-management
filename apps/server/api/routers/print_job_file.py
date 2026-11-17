from uuid import UUID

from core_domain.ids import PrintJobId
from fastapi import APIRouter, Request, Response, status

from api.common.consts import API_PREFIX, PRINT_JOBS_PATH
from api.domains.content_asset.service import FileService
from api.domains.print_job.service import PrintJobService
from api.routers.domain_errors import domain_errors_as_http

FILE_PATH = "/{print_job_id}/file"


def upload_path(print_job_id: PrintJobId) -> str:
    return f"{API_PREFIX}{PRINT_JOBS_PATH}/{print_job_id}/file"


def print_job_file_router(
    print_job_service: PrintJobService, file_service: FileService
) -> APIRouter:
    """Uploads a print job's file bytes through the job, so its rules decide. Plain HTTP because
    Connect cannot stream bytes from a browser; DeletePrintJobFile deletes the file, and downloads
    are in the file router."""
    router = APIRouter(
        prefix=PRINT_JOBS_PATH,
        tags=["Files"],
        responses={
            status.HTTP_404_NOT_FOUND: {"description": "No such print job, or no such file"},
            status.HTTP_409_CONFLICT: {
                "description": "The print job is not a draft, or it has no file"
            },
            status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "File storage is unavailable"},
        },
    )

    @router.put(
        FILE_PATH,
        status_code=status.HTTP_204_NO_CONTENT,
        responses={status.HTTP_400_BAD_REQUEST: {"description": "The bytes do not match the file"}},
    )
    async def upload_print_job_file(print_job_id: UUID, request: Request) -> Response:
        """Upload pair, call 2 of 2: the raw bytes of the file CreatePrintJobUpload attached to
        the draft."""
        with domain_errors_as_http():
            file_id = await print_job_service.draft_file(PrintJobId(print_job_id))
            await file_service.upload(file_id, request.stream())
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return router
