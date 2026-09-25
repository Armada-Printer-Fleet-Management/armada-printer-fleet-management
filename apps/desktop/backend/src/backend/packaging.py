import re

from organization_info import read

from backend.gen.common.v1 import organization_info_pb2


def executable_name() -> str:
    """The organization title without punctuation, in Train-Case: "Armada-Printer-Fleet-Management".
    Names the packaged executable and its folder; read by desktop_backend.spec and build_run.py."""
    title = read(organization_info_pb2.OrganizationInfo()).title
    return "-".join(word[0].upper() + word[1:] for word in re.findall(r"[A-Za-z0-9]+", title))
