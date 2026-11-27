from core_domain.auth import Session, User
from core_domain.ddd import Page, Service
from core_domain.ids import UserId

from armada_domains.auth.repository import SessionRepository, UserRepository


class SessionService(Service[SessionRepository]):
    def sign_in(self) -> Session:
        return self._repository.sign_in()

    def sign_out(self) -> None:
        self._repository.sign_out()

    def session(self) -> Session | None:
        return self._repository.session()


class UserService(Service[UserRepository]):
    def get(self, user_id: UserId) -> User:
        return self._repository.get(user_id)

    def page(self, page_size: int, page_token: str) -> Page[User]:
        return self._repository.page(page_size, page_token)
