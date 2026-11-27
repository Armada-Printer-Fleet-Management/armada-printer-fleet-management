"""The application server user adapter and the user IPC call, with the Connect client mocked."""

from collections.abc import Iterator
from datetime import UTC, datetime
from unittest.mock import MagicMock, create_autospec, patch

import pytest
from connectrpc.code import Code
from connectrpc.errors import ConnectError
from core_domain.auth import User, UserRole, UserStatus
from core_domain.ddd import EntityNotFound, Unavailable
from core_domain.ids import UserId
from proto_utils.gen.common.v1.page_pb2 import PageResponse
from proto_utils.gen.server.v1.user_service_pb2 import GetUserResponse, ListUsersResponse
from proto_utils.mappers import UserMapper

from armada_domains.auth.errors import SignInRequired
from armada_domains.auth.service import UserService
from armada_infrastructure.application_server.user import ApplicationServerUsers
from armada_ipc.user import UserIpc

TIME = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)


def a_user(email: str) -> User:
    # identity_provider_ref is never sent, so a user read back from the server has it empty.
    return User(
        UserId.new(), "", email, "An", "Operator", UserRole.STAFF, UserStatus.ACTIVE, TIME, TIME
    )


KNOWN = a_user("operator@example.edu")
OTHER = a_user("student@example.edu")


@pytest.fixture
def client() -> Iterator[MagicMock]:
    """The UserServiceClientSync the adapter builds, replaced by a mock."""
    target = "armada_infrastructure.application_server.user.UserServiceClientSync"
    with patch(target) as client_type:
        yield client_type.return_value


@pytest.fixture
def users(client: MagicMock) -> ApplicationServerUsers:
    return ApplicationServerUsers(MagicMock())


def test_page_sends_the_size_and_token_and_returns_entities(
    client: MagicMock, users: ApplicationServerUsers
) -> None:
    mapper = UserMapper()
    client.list_users.return_value = ListUsersResponse(
        users=[mapper.to_proto(KNOWN), mapper.to_proto(OTHER)],
        page=PageResponse(next_page_token="next"),
    )

    page = users.page(25, "abc")

    assert [vars(user) for user in page.items] == [vars(KNOWN), vars(OTHER)]
    assert page.next_page_token == "next"
    request = client.list_users.call_args.args[0]
    assert (request.page.page_size, request.page.page_token) == (25, "abc")


def test_get_returns_the_server_user_as_an_entity(
    client: MagicMock, users: ApplicationServerUsers
) -> None:
    client.get_user.return_value = GetUserResponse(user=UserMapper().to_proto(KNOWN))

    assert vars(users.get(KNOWN.id)) == vars(KNOWN)
    request = client.get_user.call_args.args[0]
    assert request.user_id.value == str(KNOWN.id)


def test_page_turns_unauthenticated_into_sign_in_required(
    client: MagicMock, users: ApplicationServerUsers
) -> None:
    client.list_users.side_effect = ConnectError(Code.UNAUTHENTICATED, "token expired")

    with pytest.raises(SignInRequired):
        users.page(25, "")


def test_get_turns_not_found_into_entity_not_found_naming_the_user(
    client: MagicMock, users: ApplicationServerUsers
) -> None:
    client.get_user.side_effect = ConnectError(Code.NOT_FOUND, "no such user")

    with pytest.raises(EntityNotFound) as raised:
        users.get(KNOWN.id)
    assert str(KNOWN.id) in str(raised.value)


def test_get_turns_an_outage_into_unavailable(
    client: MagicMock, users: ApplicationServerUsers
) -> None:
    client.get_user.side_effect = ConnectError(Code.UNAVAILABLE, "server down")

    with pytest.raises(Unavailable):
        users.get(KNOWN.id)


def test_ipc_lets_sign_in_required_reach_the_frontend() -> None:
    service = create_autospec(UserService, instance=True)
    service.page.side_effect = SignInRequired("This needs you to be signed in.")

    with pytest.raises(SignInRequired):
        UserIpc(service).list_users({"page": {"pageSize": 10}})
