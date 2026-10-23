from urllib.parse import quote
from uuid import UUID

from core_domain.ids import FileId
from fastapi import APIRouter, Request, Response, status
from fastapi.responses import StreamingResponse

from api.common.consts import API_PREFIX, FILES_PATH
from api.domains.file.service import FileService
from api.routers.domain_errors import domain_errors_as_http


def upload_path(file_id: FileId) -> str:
    return f"{API_PREFIX}{FILES_PATH}/{file_id}"


def file_router(file_service: FileService) -> APIRouter:
    """File bytes travel over plain HTTP because Connect cannot stream them from a browser. The
    service is composed in api/main.py and handed in, like the health router's checks."""
    router = APIRouter(
        prefix=FILES_PATH,
        tags=["Files"],
        responses={
            status.HTTP_404_NOT_FOUND: {"description": "No such file, or its bytes are missing"},
            status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "File storage is unavailable"},
        },
    )

    @router.put(
        "/{file_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        responses={status.HTTP_400_BAD_REQUEST: {"description": "The bytes do not match the file"}},
    )
    async def upload_file(file_id: UUID, request: Request) -> Response:
        """Upload pair, call 2 of 2: the raw bytes of a file created by a Create...Upload RPC."""
        with domain_errors_as_http():
            await file_service.upload(FileId(file_id), request.stream())
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @router.get(
        "/{file_id}",
        response_class=StreamingResponse,
        responses={status.HTTP_200_OK: {"content": {"application/octet-stream": {}}}},
    )
    async def download_file(file_id: UUID) -> StreamingResponse:
        with domain_errors_as_http():
            file, chunks = await file_service.download(FileId(file_id))
        return StreamingResponse(
            chunks,
            media_type="application/octet-stream",
            headers={
                "Content-Length": str(file.size_bytes),
                "Content-Disposition": f"attachment; filename*=UTF-8''{quote(file.filename)}",
            },
        )

    @router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_file(file_id: UUID) -> Response:
        with domain_errors_as_http():
            await file_service.delete(FileId(file_id))
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return router
