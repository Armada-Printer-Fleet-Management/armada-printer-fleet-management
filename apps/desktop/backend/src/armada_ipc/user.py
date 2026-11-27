"""Users, read from the application server through the auth domain."""

from proto_utils.gen.common.v1.page_pb2 import PageResponse
from proto_utils.gen.server.v1.user_service_pb2 import ListUsersRequest, ListUsersResponse
from proto_utils.mappers import UserMapper

from armada_domains.auth.service import UserService
from armada_ipc._base import IpcModule, proto_call


class UserIpc(IpcModule):
    _mapper = UserMapper()

    def __init__(self, users: UserService) -> None:
        self._users = users

    @proto_call(ListUsersRequest)
    def list_users(self, request: ListUsersRequest) -> ListUsersResponse:
        page = self._users.page(request.page.page_size, request.page.page_token)
        return ListUsersResponse(
            users=[self._mapper.to_proto(user) for user in page.items],
            page=PageResponse(next_page_token=page.next_page_token),
        )
