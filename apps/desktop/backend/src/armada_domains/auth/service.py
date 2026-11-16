from core_domain.auth import Session
from core_domain.ddd import Service

from armada_domains.auth.repository import SessionRepository


class SessionService(Service[SessionRepository]):
    def sign_in(self) -> Session:
        return self._repository.sign_in()

    def sign_out(self) -> None:
        self._repository.sign_out()

    def session(self) -> Session | None:
        return self._repository.session()
