from functools import cached_property

from core_domain.auth import User
from core_domain.ddd import Page
from core_domain.ids import UserId
from proto_utils.gen.common.v1.page_pb2 import PageRequest
from proto_utils.gen.id.v1 import user_id_pb2
from proto_utils.gen.server.v1.user_service_connect import UserServiceClientSync
from proto_utils.gen.server.v1.user_service_pb2 import GetUserRequest, ListUsersRequest
from proto_utils.mappers import UserMapper

from armada_domains.auth.repository import UserRepository
from armada_infrastructure.application_server.client import ApplicationServerClient
from armada_infrastructure.application_server.connection import ApplicationServerConnection


class ApplicationServerUsers(ApplicationServerClient[UserId, user_id_pb2.UserId], UserRepository):
    """Reads users from the application server."""

    _id_message_type = user_id_pb2.UserId
    _mapper = UserMapper()

    def __init__(self, server: ApplicationServerConnection) -> None:
        self._server = server

    @cached_property
    def _client(self) -> UserServiceClientSync:
        # Built on first use, so a missing server address fails the call rather than startup.
        return UserServiceClientSync(
            self._server.address(),
            http_client=self._server.http_client,
            interceptors=self._server.interceptors,
        )

    def get(self, entity_id: UserId) -> User:
        request = GetUserRequest(user_id=self._id(entity_id))
        with self._server_errors_as_domain(entity_id):
            response = self._client.get_user(request)
        return self._mapper.to_entity(response.user)

    def page(self, page_size: int, page_token: str) -> Page[User]:
        request = ListUsersRequest(page=PageRequest(page_size=page_size, page_token=page_token))
        with self._server_errors_as_domain():
            response = self._client.list_users(request)
        return Page(
            [self._mapper.to_entity(user) for user in response.users],
            response.page.next_page_token,
        )
