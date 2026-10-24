from pathlib import Path

from pyqwest import SyncClient


class ServerNotConfigured(Exception):
    def __init__(self, settings_path: Path) -> None:
        super().__init__(
            "The application server is not configured. Set server_url in "
            f"{settings_path} and restart the app."
        )


class ApplicationServerConnection:
    """The desktop's one connection to the application server. Every Connect service client is
    built on it, so they all share one HTTP connection pool instead of opening their own."""

    def __init__(self, address: str, settings_path: Path) -> None:
        self._address = address
        self._settings_path = settings_path
        self.http_client = SyncClient()

    def address(self) -> str:
        """Raises ServerNotConfigured when no address is set, so the app starts and each call
        that needs the server fails with an error saying how to fix it."""
        if not self._address:
            raise ServerNotConfigured(self._settings_path)
        return self._address
