from collections.abc import Iterable

from connectrpc.code import Code
from connectrpc.errors import ConnectError
from connectrpc.request import RequestContext
from core_domain.ids import AgreementId, UserId
from core_domain.legal import LegalDocument
from proto_utils.gen.common.v1.legal_document_pb2 import LegalDocument as LegalDocumentMessage
from proto_utils.gen.server.v1.agreement_service_pb2 import (
    AcceptAgreementRequest,
    AcceptAgreementResponse,
    GetAgreementRequest,
    GetAgreementResponse,
    ListLegalDocumentsRequest,
    ListLegalDocumentsResponse,
    ListOutstandingLegalDocumentsRequest,
    ListOutstandingLegalDocumentsResponse,
)
from proto_utils.mappers import AgreementMapper

from api.domains.legal.service import AgreementService
from api.services.domain_errors import domain_errors_as_connect, request_id


class AgreementServiceImplementation:
    """The Connect handler for server.v1.AgreementService. The domain knows each document by its
    kind and version; the title, text location and checksum clients show come from the messages
    organization.json was read into."""

    _mapper = AgreementMapper()

    def __init__(
        self, agreements: AgreementService, documents: Iterable[LegalDocumentMessage]
    ) -> None:
        self._agreements = agreements
        self._messages = {self._mapper.legal_document_from_proto(d): d for d in documents}

    def _to_proto(self, documents: Iterable[LegalDocument]) -> list[LegalDocumentMessage]:
        return [self._messages[document] for document in documents]

    async def list_legal_documents(
        self,
        request: ListLegalDocumentsRequest,
        ctx: RequestContext[ListLegalDocumentsRequest, ListLegalDocumentsResponse],
        /,
    ) -> ListLegalDocumentsResponse:
        return ListLegalDocumentsResponse(
            legal_documents=self._to_proto(self._agreements.documents())
        )

    async def list_outstanding_legal_documents(
        self,
        request: ListOutstandingLegalDocumentsRequest,
        ctx: RequestContext[
            ListOutstandingLegalDocumentsRequest, ListOutstandingLegalDocumentsResponse
        ],
        /,
    ) -> ListOutstandingLegalDocumentsResponse:
        user_id = request_id(UserId, request.user_id)
        with domain_errors_as_connect():
            documents = await self._agreements.outstanding(user_id)
        return ListOutstandingLegalDocumentsResponse(legal_documents=self._to_proto(documents))

    async def accept_agreement(
        self,
        request: AcceptAgreementRequest,
        ctx: RequestContext[AcceptAgreementRequest, AcceptAgreementResponse],
        /,
    ) -> AcceptAgreementResponse:
        user_id = request_id(UserId, request.user_id)
        version = LegalDocumentMessage(kind=request.kind, effective_date=request.effective_date)
        try:
            document = self._mapper.legal_document_from_proto(version)
        except ValueError as error:
            raise ConnectError(Code.INVALID_ARGUMENT, str(error)) from error
        with domain_errors_as_connect():
            agreement = await self._agreements.accept(user_id, document)
        return AcceptAgreementResponse(agreement=self._mapper.to_proto(agreement))

    async def get_agreement(
        self,
        request: GetAgreementRequest,
        ctx: RequestContext[GetAgreementRequest, GetAgreementResponse],
        /,
    ) -> GetAgreementResponse:
        agreement_id = request_id(AgreementId, request.agreement_id)
        with domain_errors_as_connect():
            agreement = await self._agreements.agreement(agreement_id)
        return GetAgreementResponse(agreement=self._mapper.to_proto(agreement))
