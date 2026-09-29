import re
from importlib.metadata import version

from organization_info import read
from packaging.version import Version

from armada_gen.common.v1 import organization_info_pb2


def executable_name() -> str:
    """The organization title without punctuation, in Train-Case: "Armada-Printer-Fleet-Management".
    Names the packaged executable and its folder; read by desktop_backend.spec and build_run.py."""
    title = read(organization_info_pb2.OrganizationInfo()).title
    return "-".join(word[0].upper() + word[1:] for word in re.findall(r"[A-Za-z0-9]+", title))


def installer_info() -> dict[str, str]:
    """What installer_run.py passes to installer.nsi. Windows version resources only accept
    four numbers, so `numeric_version` drops any postfix: "0.1.0-alpha" becomes "0.1.0.0"."""
    info = read(organization_info_pb2.OrganizationInfo())
    full_version = version("backend")
    release = (*Version(full_version).release, 0, 0, 0)[:4]
    return {
        "app_name": executable_name(),
        "display_name": info.title,
        "description": info.description,
        "url": info.repository_url,
        "version": full_version,
        "numeric_version": ".".join(str(part) for part in release),
    }
