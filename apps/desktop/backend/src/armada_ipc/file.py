"""File records, read from the application server through the file domain."""

from core_domain.ids import FileId
from proto_utils.gen.server.v1.file_service_pb2 import ListFilesRequest, ListFilesResponse
from proto_utils.mappers import FileMapper

from armada_domains.file.service import FileService
from armada_ipc._base import IpcModule, proto_call


class FileIpc(IpcModule):
    _mapper = FileMapper()

    def __init__(self, files: FileService) -> None:
        self._files = files

    @proto_call(ListFilesRequest)
    def list_files(self, request: ListFilesRequest) -> ListFilesResponse:
        file_ids = [self._mapper.id_from_proto(FileId, file_id) for file_id in request.file_ids]
        files = self._files.files(file_ids)
        return ListFilesResponse(files=[self._mapper.to_proto(file) for file in files])
