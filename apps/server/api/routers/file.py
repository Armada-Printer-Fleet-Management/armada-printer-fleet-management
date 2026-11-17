from urllib.parse import quote
from uuid import UUID

from core_domain.ids import FileId
from fastapi import APIRouter, status
from fastapi.responses import StreamingResponse

from api.common.consts import FILES_PATH
from api.domains.content_asset.service import FileService
from api.routers.domain_errors import domain_errors_as_http


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

    return router
