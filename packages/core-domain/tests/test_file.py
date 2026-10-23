import re
from datetime import UTC, datetime
from pathlib import Path

import pytest

from core_domain.ddd import InvalidValue
from core_domain.file import File, FileType

PROTO = Path(__file__).resolve().parents[2] / "proto" / "file" / "v1" / "file.proto"
NOW = datetime(2026, 10, 1, tzinfo=UTC)
SHA256 = "a" * 64


def test_file_type_mirrors_the_proto_enum() -> None:
    """Read as text, because core-domain may not depend on protobuf."""
    proto_values = re.findall(r"^\s*FILE_TYPE_(\w+)\s*=", PROTO.read_text(), re.MULTILINE)
    assert [v for v in proto_values if v != "UNSPECIFIED"] == [t.name for t in FileType]


def test_create_records_the_metadata() -> None:
    file = File.create("part.gcode", FileType.GCODE, 1024, SHA256, NOW)

    assert (file.filename, file.file_type, file.size_bytes, file.sha256) == (
        "part.gcode",
        FileType.GCODE,
        1024,
        SHA256,
    )
    assert file.created_at == file.updated_at == NOW


@pytest.mark.parametrize(
    ("filename", "size_bytes", "sha256"),
    [
        ("", 1024, SHA256),
        ("  ", 1024, SHA256),
        ("part.gcode", 0, SHA256),
        ("part.gcode", 1024, "A" * 64),
        ("part.gcode", 1024, "a" * 63),
        ("part.gcode", 1024, "not a hash"),
    ],
)
def test_create_refuses_invalid_metadata(filename: str, size_bytes: int, sha256: str) -> None:
    with pytest.raises(InvalidValue):
        File.create(filename, FileType.GCODE, size_bytes, sha256, NOW)


def test_check_content_accepts_the_bytes_the_file_describes() -> None:
    File.create("part.gcode", FileType.GCODE, 1024, SHA256, NOW).check_content(1024, SHA256)


@pytest.mark.parametrize(("size_bytes", "sha256"), [(1023, SHA256), (1024, "b" * 64)])
def test_check_content_refuses_other_bytes(size_bytes: int, sha256: str) -> None:
    file = File.create("part.gcode", FileType.GCODE, 1024, SHA256, NOW)
    with pytest.raises(InvalidValue):
        file.check_content(size_bytes, sha256)


def test_storage_key_is_the_content_hash_and_type() -> None:
    file = File.create("Part One.gcode", FileType.CGCODE, 1, SHA256, NOW)
    assert file.storage_key() == SHA256 + ".cgcode"


def test_files_with_the_same_content_share_a_storage_key() -> None:
    first = File.create("first.gcode", FileType.GCODE, 1, SHA256, NOW)
    second = File.create("second.gcode", FileType.GCODE, 1, SHA256, NOW)
    assert first.storage_key() == second.storage_key()


def test_the_same_content_as_another_type_has_its_own_storage_key() -> None:
    gcode = File.create("part.gcode", FileType.GCODE, 1, SHA256, NOW)
    cgcode = File.create("part.bgcode", FileType.CGCODE, 1, SHA256, NOW)
    assert gcode.storage_key() != cgcode.storage_key()
