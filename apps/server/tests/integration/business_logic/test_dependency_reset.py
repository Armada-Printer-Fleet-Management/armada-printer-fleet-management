"""The reset before each test. Each case runs twice, checking for a clean start and then leaving a
mess, so whichever run comes second fails if the reset missed anything."""

from uuid import uuid4

import pytest
import sqlalchemy as sa
from botocore.client import BaseClient

from api.infrastructure.dev_data import STUB_STUDENT_ID, stub_users
from api.infrastructure.enum_ids import FLEET_ACCESS_POLICY_STAFF_ONLY_ID
from dev_seed import SEED
from tests.integration.utils.file_store import stored_object_count

twice = pytest.mark.parametrize("run", ["first", "second"])


def _student_name() -> str:
    return next(user.display_name for user in stub_users() if user.id == STUB_STUDENT_ID)


@twice
def test_database_changes_do_not_survive(database_engine: sa.Engine, run: str) -> None:
    with database_engine.begin() as connection:
        for table, rows in SEED:
            count = connection.execute(sa.select(sa.func.count()).select_from(table)).scalar()
            assert count == len(rows), table.name
        name = connection.execute(
            sa.text("SELECT display_name FROM users WHERE id = :id"),
            {"id": STUB_STUDENT_ID.value},
        ).scalar()
        assert name == _student_name()

        connection.execute(
            sa.text(
                "INSERT INTO fleet_sections (id, name, access_policy) "
                "VALUES (:id, 'Added by a test', :access_policy)"
            ),
            {"id": uuid4(), "access_policy": FLEET_ACCESS_POLICY_STAFF_ONLY_ID},
        )
        connection.execute(
            sa.text("UPDATE users SET display_name = 'Changed by a test' WHERE id = :id"),
            {"id": STUB_STUDENT_ID.value},
        )
        connection.execute(sa.text("DELETE FROM print_jobs"))


@twice
def test_stored_objects_do_not_survive(
    file_store_client: BaseClient, stack_environment: dict[str, str], run: str
) -> None:
    bucket = stack_environment["FILE_STORE_BUCKET"]
    assert stored_object_count(file_store_client, bucket) == 0

    file_store_client.put_object(Bucket=bucket, Key="left-by-a-test.gcode", Body=b"G28")

    assert stored_object_count(file_store_client, bucket) == 1
