from collections.abc import Collection
from enum import Enum
from typing import cast
from uuid import UUID

from core_domain.auth import UserRole, UserStatus
from core_domain.content_asset import FileType
from core_domain.print_job import PrintJobStatus

from api.infrastructure import enum_ids
from api.infrastructure.enum_ids import (
    FILE_SCAN_STATUS_CLEAN_ID,
    FILE_TYPE_IDS,
    FLEET_ACCESS_POLICY_STAFF_ONLY_ID,
    PRINT_JOB_STATUS_IDS,
    USER_ROLE_IDS,
    USER_STATUS_IDS,
)


def every_stored_id() -> list[UUID]:
    """Every UUID in the module, so a newly added map or constant is checked too."""
    ids: list[UUID] = []
    for value in vars(enum_ids).values():
        if isinstance(value, UUID):
            ids.append(value)
        elif isinstance(value, dict):
            members = cast(dict[object, object], value)
            ids.extend(uuid for uuid in members.values() if isinstance(uuid, UUID))
    return ids


def test_every_domain_enum_member_has_a_stored_id() -> None:
    maps: list[tuple[type[Enum], Collection[Enum]]] = [
        (PrintJobStatus, PRINT_JOB_STATUS_IDS),
        (FileType, FILE_TYPE_IDS),
        (UserRole, USER_ROLE_IDS),
        (UserStatus, USER_STATUS_IDS),
    ]
    for enum, ids in maps:
        assert set(ids) == set(enum)


def test_seed_only_members_have_a_stored_id() -> None:
    seed_only = [
        FLEET_ACCESS_POLICY_STAFF_ONLY_ID,
        FILE_SCAN_STATUS_CLEAN_ID,
    ]
    assert set(seed_only) <= set(every_stored_id())


def test_every_stored_id_is_a_random_uuid() -> None:
    for stored_id in every_stored_id():
        assert stored_id.version == 4, stored_id


def test_no_two_members_share_a_stored_id() -> None:
    ids = every_stored_id()
    assert len(ids) == len(set(ids))
