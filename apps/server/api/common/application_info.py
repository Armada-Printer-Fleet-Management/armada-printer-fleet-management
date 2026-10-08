"""This application's own information: The application specific information"""

import tomllib
from pathlib import Path

from packaging.version import Version
from proto_utils import message_to_dict
from proto_utils.gen.common.v1 import application_info_pb2
from pydantic import BaseModel

from api.common.consts import PYPROJECT_PATH


class _Project(BaseModel):
    version: str


class _Pyproject(BaseModel):
    project: _Project


class ApplicationInfo:
    def __init__(self, pyproject_path: Path = PYPROJECT_PATH) -> None:
        with pyproject_path.open("rb") as file:
            self._version = Version(_Pyproject.model_validate(tomllib.load(file)).project.version)

    def version(self) -> dict[str, object]:
        major, minor, maintenance = (list(self._version.release) + [0, 0, 0])[:3]
        postfix = self._version.public[len(self._version.base_version) :].lstrip(".") or None
        info = application_info_pb2.VersionInfo(
            major=major,
            minor=minor,
            maintenance=maintenance,
            **({"postfix": postfix} if postfix else {}),
        )
        return message_to_dict(info)

    def version_string(self) -> str:
        version_json = self.version()
        version = f"{version_json['major']}.{version_json['minor']}.{version_json['maintenance']}"
        if postfix := version_json.get("postfix"):
            version += f"-{postfix}"
        return version
