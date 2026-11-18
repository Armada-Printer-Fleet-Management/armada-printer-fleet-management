from datetime import UTC, datetime

import pytest
from core_domain.auth import User, UserRole, UserStatus
from core_domain.ids import UserId

from proto_utils.gen.auth.v1 import user_pb2
from proto_utils.mappers import UserMapper

TIME = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)
LATER = datetime(2026, 10, 2, 9, 0, tzinfo=UTC)
OPTIONAL_TIMES = ["expires_at", "last_login_at", "deleted_at"]


def user(optional_time: datetime | None = LATER) -> User:
    """Every optional time set to optional_time. The subject is empty, as it never crosses the
    wire."""
    return User(
        id=UserId.new(),
        identity_provider_subject="",
        email="user@example.com",
        first_name="First",
        last_name="Last",
        role=UserRole.GUEST,
        status=UserStatus.SUSPENDED,
        created_at=TIME,
        updated_at=TIME,
        expires_at=optional_time,
        last_login_at=optional_time,
        deleted_at=optional_time,
    )


def test_to_entity_reverses_to_proto() -> None:
    original = user()
    assert vars(UserMapper().to_entity(UserMapper().to_proto(original))) == vars(original)


def test_the_subject_does_not_cross_the_wire() -> None:
    original = user()
    original.identity_provider_subject = "subject"
    assert UserMapper().to_entity(UserMapper().to_proto(original)).identity_provider_subject == ""


def test_unset_optional_times_stay_unset() -> None:
    message = UserMapper().to_proto(user(optional_time=None))
    assert not any(message.HasField(field) for field in OPTIONAL_TIMES)

    round_tripped = UserMapper().to_entity(message)
    assert (round_tripped.expires_at, round_tripped.last_login_at, round_tripped.deleted_at) == (
        None,
        None,
        None,
    )


def test_set_optional_times_keep_their_value() -> None:
    message = UserMapper().to_proto(user(optional_time=LATER))
    assert all(message.HasField(field) for field in OPTIONAL_TIMES)

    round_tripped = UserMapper().to_entity(message)
    assert (round_tripped.expires_at, round_tripped.last_login_at, round_tripped.deleted_at) == (
        LATER,
        LATER,
        LATER,
    )


@pytest.mark.parametrize("role", list(UserRole))
def test_every_role_maps_by_name(role: UserRole) -> None:
    original = user()
    original.role = role
    message = UserMapper().to_proto(original)

    assert user_pb2.UserRole.Name(message.role) == f"USER_ROLE_{role.name}"
    assert UserMapper().to_entity(message).role is role


@pytest.mark.parametrize("status", list(UserStatus))
def test_every_status_maps_by_name(status: UserStatus) -> None:
    original = user()
    original.status = status
    message = UserMapper().to_proto(original)

    assert user_pb2.UserStatus.Name(message.status) == f"USER_STATUS_{status.name}"
    assert UserMapper().to_entity(message).status is status


def test_to_entity_rejects_an_unspecified_role() -> None:
    message = UserMapper().to_proto(user())
    message.role = user_pb2.USER_ROLE_UNSPECIFIED
    with pytest.raises(ValueError):
        UserMapper().to_entity(message)


def test_to_entity_rejects_an_unspecified_status() -> None:
    message = UserMapper().to_proto(user())
    message.status = user_pb2.USER_STATUS_UNSPECIFIED
    with pytest.raises(ValueError):
        UserMapper().to_entity(message)
