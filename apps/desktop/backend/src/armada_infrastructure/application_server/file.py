from collections.abc import Iterable

from core_domain.file import File
from core_domain.ids import FileId
from proto_utils.gen.id.v1 import file_id_pb2
from proto_utils.gen.server.v1.file_service_connect import FileServiceClientSync
from proto_utils.gen.server.v1.file_service_pb2 import GetFileRequest, ListFilesRequest
from proto_utils.mappers import FileMapper

from armada_domains.file.repository import FileRepository
from armada_infrastructure.application_server.client import ApplicationServerClient
from armada_infrastructure.application_server.connection import ApplicationServerConnection


class ApplicationServerFiles(ApplicationServerClient[FileId, file_id_pb2.FileId], FileRepository):
    """Reads file records from the application server, which owns them."""

    _id_message_type = file_id_pb2.FileId
    _mapper = FileMapper()

    def __init__(self, server: ApplicationServerConnection) -> None:
        self._client = FileServiceClientSync(server.address, http_client=server.http_client)

    def get(self, entity_id: FileId) -> File:
        request = GetFileRequest(file_id=self._id(entity_id))
        with self._server_errors_as_domain(entity_id):
            response = self._client.get_file(request)
        return self._mapper.to_entity(response.file)

    def files(self, file_ids: Iterable[FileId]) -> list[File]:
        request = ListFilesRequest(file_ids=[self._id(file_id) for file_id in file_ids])
        with self._server_errors_as_domain():
            response = self._client.list_files(request)
        return [self._mapper.to_entity(file) for file in response.files]
