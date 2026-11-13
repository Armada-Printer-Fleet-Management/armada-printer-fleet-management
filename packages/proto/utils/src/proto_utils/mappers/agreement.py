from datetime import UTC, date

from core_domain import ids
from core_domain.legal import Agreement, LegalDocument, LegalDocumentKind

from proto_utils.gen.common.v1 import legal_document_pb2
from proto_utils.gen.common.v1.time_status_pb2 import TimeStatus
from proto_utils.gen.id.v1.agreement_id_pb2 import AgreementId
from proto_utils.gen.id.v1.user_id_pb2 import UserId
from proto_utils.gen.legal.v1 import agreement_pb2
from proto_utils.mapper import ProtoMapper

_KIND_PREFIX = "LEGAL_DOCUMENT_KIND_"


class AgreementMapper(ProtoMapper[Agreement, agreement_pb2.Agreement]):
    def to_proto(self, entity: Agreement) -> agreement_pb2.Agreement:
        return agreement_pb2.Agreement(
            id=self.id_to_proto(AgreementId, entity.id),
            user_id=self.id_to_proto(UserId, entity.user_id),
            kind=self.kind_to_proto(entity.kind),
            effective_date=entity.effective_date.isoformat(),
            time_status=TimeStatus(created_at=entity.created_at, updated_at=entity.updated_at),
        )

    def to_entity(self, message: agreement_pb2.Agreement) -> Agreement:
        return Agreement(
            id=self.id_from_proto(ids.AgreementId, message.id),
            user_id=self.id_from_proto(ids.UserId, message.user_id),
            kind=self.kind_from_proto(message.kind),
            effective_date=date.fromisoformat(message.effective_date),
            created_at=message.time_status.created_at.ToDatetime(UTC),
            updated_at=message.time_status.updated_at.ToDatetime(UTC),
        )

    @staticmethod
    def legal_document_from_proto(message: legal_document_pb2.LegalDocument) -> LegalDocument:
        """The version a document message names. Raises ValueError for an unknown kind or a date
        that is not YYYY-MM-DD."""
        return LegalDocument(
            AgreementMapper.kind_from_proto(message.kind),
            date.fromisoformat(message.effective_date),
        )

    @staticmethod
    def kind_to_proto(kind: LegalDocumentKind) -> str:
        """The enum value's name, which every message constructor accepts."""
        return _KIND_PREFIX + kind.name

    @staticmethod
    def kind_from_proto(kind: legal_document_pb2.LegalDocumentKind) -> LegalDocumentKind:
        """Raises ValueError for LEGAL_DOCUMENT_KIND_UNSPECIFIED or a value this build does not
        know."""
        name = legal_document_pb2.LegalDocumentKind.Name(kind).removeprefix(_KIND_PREFIX)
        if name not in LegalDocumentKind.__members__:
            raise ValueError(f"{_KIND_PREFIX}{name} is not a valid legal document kind")
        return LegalDocumentKind[name]
