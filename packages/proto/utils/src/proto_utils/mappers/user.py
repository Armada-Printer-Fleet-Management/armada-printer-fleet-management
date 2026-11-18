from datetime import UTC, datetime

from core_domain import ids
from core_domain.auth import User, UserRole, UserStatus
from google.protobuf.timestamp_pb2 import Timestamp

from proto_utils.gen.auth.v1 import user_pb2
from proto_utils.gen.common.v1.time_status_pb2 import TimeStatus
from proto_utils.gen.id.v1.user_id_pb2 import UserId
from proto_utils.mapper import ProtoMapper

_ROLE_PREFIX = "USER_ROLE_"
_STATUS_PREFIX = "USER_STATUS_"


class UserMapper(ProtoMapper[User, user_pb2.User]):
    def to_proto(self, entity: User) -> user_pb2.User:
        return user_pb2.User(
            id=self.id_to_proto(UserId, entity.id),
            email=entity.email,
            first_name=entity.first_name,
            last_name=entity.last_name,
            role=_ROLE_PREFIX + entity.role.name,
            status=_STATUS_PREFIX + entity.status.name,
            expires_at=entity.expires_at,
            last_login_at=entity.last_login_at,
            deleted_at=entity.deleted_at,
            time_status=TimeStatus(created_at=entity.created_at, updated_at=entity.updated_at),
        )

    def to_entity(self, message: user_pb2.User) -> User:
        """identity_provider_subject is never sent, so the entity comes back with it empty."""
        return User(
            id=self.id_from_proto(ids.UserId, message.id),
            identity_provider_subject="",
            email=message.email,
            first_name=message.first_name,
            last_name=message.last_name,
            role=self.role_from_proto(message.role),
            status=self.status_from_proto(message.status),
            created_at=message.time_status.created_at.ToDatetime(UTC),
            updated_at=message.time_status.updated_at.ToDatetime(UTC),
            expires_at=_optional_time(message, "expires_at"),
            last_login_at=_optional_time(message, "last_login_at"),
            deleted_at=_optional_time(message, "deleted_at"),
        )

    @staticmethod
    def role_from_proto(role: user_pb2.UserRole) -> UserRole:
        """Raises ValueError for USER_ROLE_UNSPECIFIED or a value this build does not know."""
        name = user_pb2.UserRole.Name(role).removeprefix(_ROLE_PREFIX)
        if name not in UserRole.__members__:
            raise ValueError(f"{_ROLE_PREFIX}{name} is not a valid user role")
        return UserRole[name]

    @staticmethod
    def status_from_proto(status: user_pb2.UserStatus) -> UserStatus:
        """Raises ValueError for USER_STATUS_UNSPECIFIED or a value this build does not know."""
        name = user_pb2.UserStatus.Name(status).removeprefix(_STATUS_PREFIX)
        if name not in UserStatus.__members__:
            raise ValueError(f"{_STATUS_PREFIX}{name} is not a valid user status")
        return UserStatus[name]


def _optional_time(message: user_pb2.User, field: str) -> datetime | None:
    if not message.HasField(field):
        return None
    timestamp: Timestamp = getattr(message, field)
    return timestamp.ToDatetime(UTC)
