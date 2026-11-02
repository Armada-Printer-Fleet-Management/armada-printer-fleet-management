"""ID column naming rules for the database, the schema's version of the proto typed-ID rules.
Every migration up to head is rendered as SQL offline, so no database is needed."""

import io
import re
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

ALEMBIC_INI = Path(__file__).parents[2] / "alembic.ini"
PROTO_IDS = Path(__file__).parents[4] / "packages" / "proto" / "id" / "v1"

CREATE_TABLE = re.compile(r"^CREATE TABLE (\w+) \((.*)\)$", re.S)
RENAME_TABLE = re.compile(r"^ALTER TABLE (\w+) RENAME TO (\w+)$")
DROP_TABLE = re.compile(r"^DROP TABLE (\w+)$")
ADD_COLUMN = re.compile(r"^ALTER TABLE (\w+) ADD COLUMN (\w+)")
DROP_COLUMN = re.compile(r"^ALTER TABLE (\w+) DROP COLUMN (\w+)")
RENAME_COLUMN = re.compile(r"^ALTER TABLE (\w+) RENAME COLUMN (\w+) TO (\w+)$")

Schema = dict[str, set[str]]


def _snake(camel: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", camel).lower()


def _singular(table: str) -> str:
    if table.endswith("ies"):
        return table.removesuffix("ies") + "y"
    return table.removesuffix("s")


def _schema(sql: str) -> Schema:
    """Replays the DDL statements in order, so later migrations' renames and drops count."""
    tables: Schema = {}
    for statement in (s.strip() for s in sql.split(";")):
        if match := CREATE_TABLE.match(statement):
            lines = (line.strip() for line in match[2].splitlines())
            # Constraint lines start with an upper-case keyword; column names never do.
            words = (line.split()[0] for line in lines if line)
            tables[match[1]] = {word for word in words if not word.isupper()}
        elif match := RENAME_TABLE.match(statement):
            tables[match[2]] = tables.pop(match[1])
        elif match := DROP_TABLE.match(statement):
            tables.pop(match[1])
        elif match := ADD_COLUMN.match(statement):
            tables[match[1]].add(match[2])
        elif match := DROP_COLUMN.match(statement):
            tables[match[1]].discard(match[2])
        elif match := RENAME_COLUMN.match(statement):
            tables[match[1]].discard(match[2])
            tables[match[1]].add(match[3])
    return tables


def _entities(tables: Schema) -> set[str]:
    """What an ID column may point at: an id/v1 typed ID, or a table in the schema."""
    typed_ids = {
        _snake(name)
        for proto in PROTO_IDS.glob("*.proto")
        for name in re.findall(r"^message (\w+)Id\b", proto.read_text(), re.MULTILINE)
    }
    return typed_ids | {_singular(table) for table in tables}


def problems(tables: Schema, entities: set[str]) -> list[str]:
    found: list[str] = []
    for table, columns in sorted(tables.items()):
        for column in sorted(c for c in columns if c.endswith("_id")):
            if column == "target_id":
                if "target_type" not in columns:
                    found.append(f"{table}.target_id needs target_type beside it")
            elif column.removesuffix("_id") not in entities:
                found.append(
                    f"{table}.{column}: an ID column is <entity>_id with no prefix; an"
                    " identifier from outside the database is named <name>_ref"
                )
    return found


@pytest.fixture(scope="module")
def schema() -> Schema:
    with pytest.MonkeyPatch.context() as env:
        # Offline mode never connects, but the migration environment still builds a URL.
        for name in ("DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"):
            env.setenv(name, "offline")
        buffer = io.StringIO()
        command.upgrade(Config(ALEMBIC_INI, output_buffer=buffer), "head", sql=True)
    return _schema(buffer.getvalue())


def test_every_id_column_names_an_entity(schema: Schema) -> None:
    assert "print_job_id" in schema["print_job_events"], "the DDL was not parsed"
    assert problems(schema, _entities(schema)) == []


def test_target_id_is_allowed_only_beside_target_type() -> None:
    assert problems({"audit_logs": {"target_type", "target_id"}}, set()) == []
    assert problems({"audit_logs": {"target_id"}}, set()) == [
        "audit_logs.target_id needs target_type beside it"
    ]


def test_an_external_id_is_told_to_use_ref() -> None:
    [problem] = problems({"users": {"keycloak_user_id"}}, {"user"})
    assert "users.keycloak_user_id" in problem
    assert "_ref" in problem


def test_a_prefixed_id_is_rejected() -> None:
    [problem] = problems({"print_jobs": {"assigned_printer_id"}}, {"printer", "print_job"})
    assert problem.startswith("print_jobs.assigned_printer_id")
