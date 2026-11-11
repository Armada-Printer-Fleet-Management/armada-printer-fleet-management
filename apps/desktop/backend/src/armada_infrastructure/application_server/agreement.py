from functools import cached_property

from core_domain.ids import AgreementId, UserId
from core_domain.legal import Agreement, LegalDocument
from proto_utils.gen.id.v1 import agreement_id_pb2, user_id_pb2
from proto_utils.gen.server.v1.agreement_service_connect import AgreementServiceClientSync
from proto_utils.gen.server.v1.agreement_service_pb2 import (
    AcceptAgreementRequest,
    GetAgreementRequest,
    ListOutstandingLegalDocumentsRequest,
)
from proto_utils.mappers import AgreementMapper

from armada_domains.legal.repository import AgreementRepository
from armada_infrastructure.application_server.client import ApplicationServerClient
from armada_infrastructure.application_server.connection import ApplicationServerConnection


class ApplicationServerAgreements(
    ApplicationServerClient[AgreementId, agreement_id_pb2.AgreementId], AgreementRepository
):
    """Reads agreements from the application server, which owns them, and asks it to record one."""

    _id_message_type = agreement_id_pb2.AgreementId
    _mapper = AgreementMapper()

    def __init__(self, server: ApplicationServerConnection) -> None:
        self._server = server

    @cached_property
    def _client(self) -> AgreementServiceClientSync:
        # Built on first use, so a missing server address fails the call rather than startup.
        return AgreementServiceClientSync(
            self._server.address(), http_client=self._server.http_client
        )

    def get(self, entity_id: AgreementId) -> Agreement:
        request = GetAgreementRequest(agreement_id=self._id(entity_id))
        with self._server_errors_as_domain(entity_id):
            response = self._client.get_agreement(request)
        return self._mapper.to_entity(response.agreement)

    def outstanding(self, user_id: UserId) -> list[LegalDocument]:
        # With no server set there is nowhere to record acceptance, server must be configured
        if not self._server.is_configured():
            return []
        request = ListOutstandingLegalDocumentsRequest(user_id=self._user_id(user_id))
        with self._server_errors_as_domain():
            response = self._client.list_outstanding_legal_documents(request)
        return [self._mapper.legal_document_from_proto(d) for d in response.legal_documents]

    def request_accept(self, user_id: UserId, document: LegalDocument) -> Agreement:
        request = AcceptAgreementRequest(
            user_id=self._user_id(user_id),
            kind=self._mapper.kind_to_proto(document.kind),
            effective_date=document.effective_date.isoformat(),
        )
        with self._server_errors_as_domain():
            response = self._client.accept_agreement(request)
        return self._mapper.to_entity(response.agreement)

    def _user_id(self, user_id: UserId) -> user_id_pb2.UserId:
        return self._mapper.id_to_proto(user_id_pb2.UserId, user_id)
