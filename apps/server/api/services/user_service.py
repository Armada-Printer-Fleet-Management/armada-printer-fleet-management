from datetime import UTC

from connectrpc.code import Code
from connectrpc.errors import ConnectError
from connectrpc.request import RequestContext
from core_domain.ids import UserId
from proto_utils.gen.common.v1.page_pb2 import PageResponse
from proto_utils.gen.server.v1.user_service_pb2 import (
    CreateUserRequest,
    CreateUserResponse,
    GetUserRequest,
    GetUserResponse,
    ListUsersRequest,
    ListUsersResponse,
    TransitionUserRoleRequest,
    TransitionUserRoleResponse,
    TransitionUserStatusRequest,
    TransitionUserStatusResponse,
    UpdateUserRequest,
    UpdateUserResponse,
)
from proto_utils.mappers import UserMapper

from api.domains.auth.service import UserService
from api.services.domain_errors import domain_errors_as_connect, request_id


def _not_implemented() -> ConnectError:
    return ConnectError(Code.UNIMPLEMENTED, "This procedure is not implemented yet")


class UserServiceImplementation:
    """The Connect handler for server.v1.UserService."""

    _mapper = UserMapper()

    def __init__(self, users: UserService) -> None:
        self._users = users

    async def get_user(
        self,
        request: GetUserRequest,
        ctx: RequestContext[GetUserRequest, GetUserResponse],
        /,
    ) -> GetUserResponse:
        user_id = request_id(UserId, request.user_id)
        with domain_errors_as_connect():
            user = await self._users.user(user_id)
        return GetUserResponse(user=self._mapper.to_proto(user))

    async def create_user(
        self,
        request: CreateUserRequest,
        ctx: RequestContext[CreateUserRequest, CreateUserResponse],
        /,
    ) -> CreateUserResponse:
        try:
            role = UserMapper.role_from_proto(request.role)
        except ValueError as error:
            raise ConnectError(Code.INVALID_ARGUMENT, "role must be set") from error
        expires_at = request.expires_at.ToDatetime(UTC) if request.HasField("expires_at") else None
        with domain_errors_as_connect():
            user = await self._users.create(
                request.email, request.first_name, request.last_name, role, expires_at
            )
        return CreateUserResponse(user=self._mapper.to_proto(user))

    async def list_users(
        self,
        request: ListUsersRequest,
        ctx: RequestContext[ListUsersRequest, ListUsersResponse],
        /,
    ) -> ListUsersResponse:
        with domain_errors_as_connect():
            page = await self._users.page(request.page.page_size, request.page.page_token)
        return ListUsersResponse(
            users=[self._mapper.to_proto(user) for user in page.items],
            page=PageResponse(next_page_token=page.next_page_token),
        )

    async def update_user(
        self,
        request: UpdateUserRequest,
        ctx: RequestContext[UpdateUserRequest, UpdateUserResponse],
        /,
    ) -> UpdateUserResponse:
        raise _not_implemented()

    async def transition_user_status(
        self,
        request: TransitionUserStatusRequest,
        ctx: RequestContext[TransitionUserStatusRequest, TransitionUserStatusResponse],
        /,
    ) -> TransitionUserStatusResponse:
        user_id = request_id(UserId, request.user_id)
        with domain_errors_as_connect():
            match request.WhichOneof("action"):
                case "suspend":
                    user = await self._users.suspend(user_id)
                case "reactivate":
                    user = await self._users.activate(user_id)
                case "delete":
                    user = await self._users.delete(user_id)
                case _:
                    raise ConnectError(Code.INVALID_ARGUMENT, "action must be set")
        return TransitionUserStatusResponse(user=self._mapper.to_proto(user))

    async def transition_user_role(
        self,
        request: TransitionUserRoleRequest,
        ctx: RequestContext[TransitionUserRoleRequest, TransitionUserRoleResponse],
        /,
    ) -> TransitionUserRoleResponse:
        raise _not_implemented()
