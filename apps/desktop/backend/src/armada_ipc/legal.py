"""The legal documents this app's user must accept, and their acceptance, through the legal
domain."""

from collections.abc import Iterable

from core_domain.legal import LegalDocument
from proto_utils.gen.common.v1.legal_document_pb2 import LegalDocument as LegalDocumentMessage
from proto_utils.gen.server.v1.agreement_service_pb2 import (
    AcceptAgreementRequest,
    AcceptAgreementResponse,
    ListOutstandingLegalDocumentsResponse,
)
from proto_utils.mappers import AgreementMapper

from armada_domains.legal.service import AgreementService
from armada_ipc._base import IpcModule, proto_call, proto_response


class LegalIpc(IpcModule):
    """The server knows a document by its kind and version; its title and checksum come from
    the messages this build's organization.json was read into."""

    _mapper = AgreementMapper()

    def __init__(
        self, agreements: AgreementService, documents: Iterable[LegalDocumentMessage]
    ) -> None:
        self._agreements = agreements
        self._messages = {self._mapper.legal_document_from_proto(d): d for d in documents}

    def _message(self, document: LegalDocument) -> LegalDocumentMessage:
        # A version this build does not ship still goes back by kind and date, so the frontend
        # can say the app is out of date instead of showing the wrong text.
        return self._messages.get(document) or LegalDocumentMessage(
            kind=self._mapper.kind_to_proto(document.kind),
            effective_date=document.effective_date.isoformat(),
        )

    @proto_response
    def outstanding_legal_documents(self) -> ListOutstandingLegalDocumentsResponse:
        documents = self._agreements.outstanding()
        return ListOutstandingLegalDocumentsResponse(
            legal_documents=[self._message(d) for d in documents]
        )

    @proto_call(AcceptAgreementRequest)
    def accept_agreement(self, request: AcceptAgreementRequest) -> AcceptAgreementResponse:
        """request.user_id is ignored: the agreement is always for this app's own user."""
        version = LegalDocumentMessage(kind=request.kind, effective_date=request.effective_date)
        agreement = self._agreements.accept(self._mapper.legal_document_from_proto(version))
        return AcceptAgreementResponse(agreement=self._mapper.to_proto(agreement))
