from core_domain.ids import PrintJobId
from core_domain.print_job import PrintJob
from proto_utils.gen.id.v1 import print_job_id_pb2
from proto_utils.gen.server.v1.print_job_service_connect import PrintJobServiceClientSync
from proto_utils.gen.server.v1.print_job_service_pb2 import (
    GetPrintJobRequest,
    TransitionPrintJobRequest,
)
from proto_utils.mappers import PrintJobMapper

from armada_infrastructure.application_server.client import ApplicationServerClient
from armada_infrastructure.application_server.connection import ApplicationServerConnection


class ApplicationServerPrintJobs(ApplicationServerClient[PrintJobId, print_job_id_pb2.PrintJobId]):
    """Reads print jobs from the application server, which owns them, and asks it for changes."""

    _id_message_type = print_job_id_pb2.PrintJobId
    _mapper = PrintJobMapper()

    def __init__(self, server: ApplicationServerConnection) -> None:
        self._client = PrintJobServiceClientSync(server.address, http_client=server.http_client)

    def get(self, entity_id: PrintJobId) -> PrintJob:
        request = GetPrintJobRequest(print_job_id=self._id(entity_id))
        with self._server_errors_as_domain(entity_id):
            response = self._client.get_print_job(request)
        return self._mapper.to_entity(response.print_job)

    def request_start_review(self, print_job_id: PrintJobId) -> PrintJob:
        request = TransitionPrintJobRequest(
            print_job_id=self._id(print_job_id),
            start_review=TransitionPrintJobRequest.StartReview(),
        )
        with self._server_errors_as_domain(print_job_id):
            response = self._client.transition_print_job(request)
        return self._mapper.to_entity(response.print_job)
