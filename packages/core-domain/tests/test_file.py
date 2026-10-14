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
