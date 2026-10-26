from connectrpc.request import RequestContext
from core_domain.ids import FileId
from proto_utils.gen.server.v1.file_service_pb2 import (
    GetFileRequest,
    GetFileResponse,
    ListFilesRequest,
    ListFilesResponse,
)
from proto_utils.mappers import FileMapper

from api.domains.file.service import FileService
from api.services.domain_errors import domain_errors_as_connect, request_id


class FileServiceImplementation:
    """The Connect handler for server.v1.FileService."""

    _mapper = FileMapper()

    def __init__(self, files: FileService) -> None:
        self._files = files

    async def list_files(
        self,
        request: ListFilesRequest,
        ctx: RequestContext[ListFilesRequest, ListFilesResponse],
        /,
    ) -> ListFilesResponse:
        file_ids = [request_id(FileId, file_id) for file_id in request.file_ids]
        with domain_errors_as_connect():
            files = await self._files.files(file_ids)
        return ListFilesResponse(files=[self._mapper.to_proto(file) for file in files])

    async def get_file(
        self,
        request: GetFileRequest,
        ctx: RequestContext[GetFileRequest, GetFileResponse],
        /,
    ) -> GetFileResponse:
        file_id = request_id(FileId, request.file_id)
        with domain_errors_as_connect():
            file = await self._files.file(file_id)
        return GetFileResponse(file=self._mapper.to_proto(file))
