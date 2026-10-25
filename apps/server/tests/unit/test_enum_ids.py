from enum import Enum
from uuid import UUID

from core_domain.file import FileType
from core_domain.print_job import PrintJobStatus
from proto_utils.gen.user.v1 import user_pb2

from api.infrastructure import enum_ids
from api.infrastructure.enum_ids import (
    FILE_SCAN_STATUS_CLEAN_ID,
    FILE_TYPE_IDS,
    FILE_UPLOAD_STATUS_UPLOADED_ID,
    FLEET_ACCESS_POLICY_STAFF_ONLY_ID,
    PRINT_JOB_STATUS_IDS,
    USER_ROLE_IDS,
    USER_STATUS_ACTIVE_ID,
)


def every_stored_id() -> list[UUID]:
    """Every UUID in the module, so a newly added map or constant is checked too."""
    ids: list[UUID] = []
    for value in vars(enum_ids).values():
        if isinstance(value, UUID):
            ids.append(value)
        elif isinstance(value, dict):
            ids.extend(uuid for uuid in value.values() if isinstance(uuid, UUID))
    return ids


def test_every_domain_enum_member_has_a_stored_id() -> None:
    maps: list[tuple[type[Enum], dict[PrintJobStatus, UUID] | dict[FileType, UUID]]] = [
        (PrintJobStatus, PRINT_JOB_STATUS_IDS),
        (FileType, FILE_TYPE_IDS),
    ]
    for enum, ids in maps:
        assert set(ids) == set(enum)


def test_every_user_role_but_unspecified_has_a_stored_id() -> None:
    roles = set(user_pb2.UserRole.values()) - {user_pb2.USER_ROLE_UNSPECIFIED}
    assert set(USER_ROLE_IDS) == roles


def test_seed_only_members_have_a_stored_id() -> None:
    seed_only = [
        USER_STATUS_ACTIVE_ID,
        FLEET_ACCESS_POLICY_STAFF_ONLY_ID,
        FILE_UPLOAD_STATUS_UPLOADED_ID,
        FILE_SCAN_STATUS_CLEAN_ID,
    ]
    assert set(seed_only) <= set(every_stored_id())


def test_every_stored_id_is_a_random_uuid() -> None:
    for stored_id in every_stored_id():
        assert stored_id.version == 4, stored_id


def test_no_two_members_share_a_stored_id() -> None:
    ids = every_stored_id()
    assert len(ids) == len(set(ids))
