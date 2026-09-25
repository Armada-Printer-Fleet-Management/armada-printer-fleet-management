from pathlib import Path

import pytest
from pydantic import ValidationError

from api.common.application_information import ApplicationInformation


def write_pyproject(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "pyproject.toml"
    path.write_text(body)
    return path


def test_release_version_has_no_postfix(tmp_path: Path) -> None:
    path = write_pyproject(tmp_path, '[project]\nversion = "0.1.0"\n')

    assert ApplicationInformation(path).version() == {"major": 0, "minor": 1, "maintenance": 0}


def test_special_release_version_carries_postfix(tmp_path: Path) -> None:
    path = write_pyproject(tmp_path, '[project]\nversion = "1.2.3-rc1"\n')

    assert ApplicationInformation(path).version() == {
        "major": 1,
        "minor": 2,
        "maintenance": 3,
        "postfix": "rc1",
    }


def test_short_version_pads_missing_parts_with_zero(tmp_path: Path) -> None:
    path = write_pyproject(tmp_path, '[project]\nversion = "2"\n')

    assert ApplicationInformation(path).version() == {"major": 2, "minor": 0, "maintenance": 0}


def test_missing_file_fails_at_construction(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        ApplicationInformation(tmp_path / "pyproject.toml")


def test_missing_project_version_fails_at_construction(tmp_path: Path) -> None:
    path = write_pyproject(tmp_path, '[project]\nname = "server"\n')

    with pytest.raises(ValidationError):
        ApplicationInformation(path)
