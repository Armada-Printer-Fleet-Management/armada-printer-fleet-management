from core_domain import ids
from core_domain.auth import Session

from proto_utils.gen.auth.v1 import session_pb2
from proto_utils.gen.id.v1.session_id_pb2 import SessionId
from proto_utils.mapper import ProtoMapper


class SessionMapper(ProtoMapper[Session, session_pb2.Session]):
    def to_proto(self, entity: Session) -> session_pb2.Session:
        return session_pb2.Session(
            id=self.id_to_proto(SessionId, entity.id),
            email=entity.email,
            first_name=entity.first_name,
            last_name=entity.last_name,
        )

    def to_entity(self, message: session_pb2.Session) -> Session:
        return Session(
            id=self.id_from_proto(ids.SessionId, message.id),
            email=message.email,
            first_name=message.first_name,
            last_name=message.last_name,
        )
