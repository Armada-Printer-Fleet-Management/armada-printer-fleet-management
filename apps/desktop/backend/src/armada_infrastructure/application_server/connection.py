from pyqwest import SyncClient

# TODO: HARDCODED FOR DEVELOPMENT. This is the dev compose server's address, so the desktop can
# only reach a server running on this machine. It is replaced by the desktop connection settings
# file (ARM-147).
SERVER_URL = "http://localhost:8000/api"


class ApplicationServerConnection:
    """The desktop's one connection to the application server. Every Connect service client is
    built on it, so they all share one HTTP connection pool instead of opening their own."""

    def __init__(self, address: str = SERVER_URL) -> None:
        self.address = address
        self.http_client = SyncClient()
