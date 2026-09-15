import webview

from backend.ipc import Ipc


def run(target: str) -> None:
    """target is a URL or a file:// URI, depending on application boot mode."""
    webview.create_window(  # pyright: ignore[reportUnknownMemberType]
        "Armada - Printer Fleet Management", url=target, js_api=Ipc()
    )
    webview.start()
