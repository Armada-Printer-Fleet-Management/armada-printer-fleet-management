from importlib.resources import files

from google.protobuf.json_format import Parse
from google.protobuf.message import Message


def read[M: Message](message: M) -> M:
    """Fills `message` from organization.json and returns it. The caller passes an instance of
    its own generated common.v1.OrganizationInfo, so this package never depends on one app's
    generated code."""
    text = files("organization_info").joinpath("organization.json").read_text(encoding="utf-8")
    Parse(text, message)
    return message


__all__ = ["read"]
