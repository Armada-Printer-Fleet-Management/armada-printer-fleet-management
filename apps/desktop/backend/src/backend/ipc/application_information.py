from importlib.metadata import version as pkg_version

from packaging.version import Version
from proto_utils import message_to_dict

from backend.gen.common.v1 import application_information_pb2
from backend.ipc._base import IpcModule


class ApplicationInformation(IpcModule):
    def version(self) -> dict[str, object]:
        parsed = Version(pkg_version("backend"))
        major, minor, maintenance = (list(parsed.release) + [0, 0, 0])[:3]
        postfix = parsed.public[len(parsed.base_version) :].lstrip(".") or None
        info = application_information_pb2.VersionInfo(
            major=major,
            minor=minor,
            maintenance=maintenance,
            **({"postfix": postfix} if postfix else {}),
        )
        return message_to_dict(info)
