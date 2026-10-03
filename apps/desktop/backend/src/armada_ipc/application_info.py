"""This application's own information: The application specific information"""

from importlib.metadata import version as pkg_version

from packaging.version import Version

from armada_gen.common.v1 import application_info_pb2
from armada_ipc._base import IpcModule, proto_response


class ApplicationInfo(IpcModule):
    @proto_response
    def version(self) -> application_info_pb2.VersionInfo:
        parsed = Version(pkg_version("backend"))
        major, minor, maintenance = (list(parsed.release) + [0, 0, 0])[:3]
        postfix = parsed.public[len(parsed.base_version) :].lstrip(".") or None
        return application_info_pb2.VersionInfo(
            major=major,
            minor=minor,
            maintenance=maintenance,
            **({"postfix": postfix} if postfix else {}),
        )
