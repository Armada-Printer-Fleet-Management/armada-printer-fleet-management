import asyncio
from datetime import UTC, datetime

import pytest
from core_domain.ddd import EntityNotFound, InvalidValue
from core_domain.file import FileType
from core_domain.ids import FileId

from api.domains.file.service import FileService
from api.infrastructure.file_memory import InMemoryFileRepository
from api.infrastructure.file_storage_mock import MockFileStorage

NOW = datetime(2026, 10, 7, 12, 0, tzinfo=UTC)
SHA256 = "d" * 64


@pytest.fixture
def service() -> FileService:
    return FileService(InMemoryFileRepository(), MockFileStorage(), clock=lambda: NOW)


def test_create_upload_saves_the_file_and_returns_its_upload_url(service: FileService) -> None:
    file, upload_url = asyncio.run(
        service.create_upload("part.gcode", FileType.GCODE, 1024, SHA256)
    )

    stored = asyncio.run(service.file(file.id))
    assert (stored.filename, stored.size_bytes, stored.created_at) == ("part.gcode", 1024, NOW)
    assert str(file.id) in upload_url


def test_create_upload_refused_by_the_rule_saves_nothing(service: FileService) -> None:
    with pytest.raises(InvalidValue):
        asyncio.run(service.create_upload("part.gcode", FileType.GCODE, 0, SHA256))


def test_is_uploaded_asks_storage_about_a_known_file(service: FileService) -> None:
    file, _ = asyncio.run(service.create_upload("part.gcode", FileType.GCODE, 1024, SHA256))
    assert asyncio.run(service.is_uploaded(file.id))


def test_is_uploaded_reports_an_unknown_file(service: FileService) -> None:
    with pytest.raises(EntityNotFound):
        asyncio.run(service.is_uploaded(FileId.new()))
