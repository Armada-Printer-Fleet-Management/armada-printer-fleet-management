from connectrpc.code import Code
from connectrpc.errors import ConnectError
from core_domain.ddd import EntityNotFound
from core_domain.ids import PrintJobId
from core_domain.print_job import PrintJob
from proto_utils.gen.id.v1 import print_job_id_pb2
from proto_utils.gen.server.v1.print_job_service_connect import PrintJobServiceClientSync
from proto_utils.gen.server.v1.print_job_service_pb2 import GetPrintJobRequest
from proto_utils.mappers import PrintJobMapper

from armada_infrastructure.application_server.connection import ApplicationServerConnection


class ApplicationServerPrintJobRepository:
    """Reads print jobs from the application server, which owns them."""

    _mapper = PrintJobMapper()

    def __init__(self, server: ApplicationServerConnection) -> None:
        self._client = PrintJobServiceClientSync(server.address, http_client=server.http_client)

    def get(self, entity_id: PrintJobId) -> PrintJob:
        request = GetPrintJobRequest(
            print_job_id=self._mapper.id_to_proto(print_job_id_pb2.PrintJobId, entity_id)
        )
        try:
            response = self._client.get_print_job(request)
        except ConnectError as error:
            if error.code is Code.NOT_FOUND:
                raise EntityNotFound(entity_id) from error
            raise
        return self._mapper.to_entity(response.print_job)
