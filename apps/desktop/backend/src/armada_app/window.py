import webview
from organization_info import read
from proto_utils.gen.common.v1 import organization_info_pb2

from armada_app.composition import build_ipc


def run(target: str) -> None:
    """target is a URL or a file:// URI, depending on application boot mode."""
    title = read(organization_info_pb2.OrganizationInfo()).title
    webview.create_window(  # pyright: ignore[reportUnknownMemberType]
        title, url=target, js_api=build_ipc()
    )
    webview.start()
