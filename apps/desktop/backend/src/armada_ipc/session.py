"""The operator's sign-in, through the auth domain. Tokens never cross IPC; only the session's
display state does."""

from core_domain.auth import Session
from proto_utils.gen.desktop.v1 import current_session_pb2
from proto_utils.mappers import SessionMapper

from armada_domains.auth.service import SessionService
from armada_ipc._base import IpcModule, proto_response


class SessionIpc(IpcModule):
    _mapper = SessionMapper()

    def __init__(self, sessions: SessionService) -> None:
        self._sessions = sessions

    @proto_response
    def sign_in(self) -> current_session_pb2.CurrentSession:
        """Opens the browser and resolves once the operator has signed in there."""
        return self._current(self._sessions.sign_in())

    @proto_response
    def sign_out(self) -> current_session_pb2.CurrentSession:
        self._sessions.sign_out()
        return self._current(None)

    @proto_response
    def session(self) -> current_session_pb2.CurrentSession:
        return self._current(self._sessions.session())

    def _current(self, session: Session | None) -> current_session_pb2.CurrentSession:
        if session is None:
            return current_session_pb2.CurrentSession()
        return current_session_pb2.CurrentSession(session=self._mapper.to_proto(session))
