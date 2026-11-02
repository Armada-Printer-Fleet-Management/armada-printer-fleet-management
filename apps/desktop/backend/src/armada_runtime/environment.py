import os
import sys
from pathlib import Path

from armada_runtime.packaging import executable_name


class Environment:
    """Where this process is running, and how to find bundled resources from here.

    Dev: running from source (uv run, dev_run.py); resources live in the repo tree.
    Frozen: running from the PyInstaller build; resources sit where desktop_backend.spec's
    `datas` put them. Ask this class for a path instead of checking sys.frozen elsewhere."""

    is_dev: bool = not getattr(sys, "frozen", False)

    @staticmethod
    def resource_root() -> Path:
        if Environment.is_dev:
            return Path(__file__).resolve().parents[3]  # apps/desktop/
        # PyInstaller's bundle directory: `_internal/` beside the exe in an onedir build.
        bundle: str = getattr(sys, "_MEIPASS", str(Path(sys.executable).parent))
        return Path(bundle)

    @staticmethod
    def resource_path(*parts: str) -> Path:
        return Environment.resource_root().joinpath(*parts)

    @staticmethod
    def default_frontend_target() -> str:
        return Environment.resource_path("frontend", "dist", "index.html").as_uri()

    @staticmethod
    def user_data_dir() -> Path:
        """`%APPDATA%/<exe name>`: per-user files that outlive an uninstall."""
        app_data = os.environ.get("APPDATA")
        if not app_data:
            raise RuntimeError("APPDATA is not set, so there is nowhere to keep per-user files")
        return Path(app_data) / executable_name()

    @staticmethod
    def settings_path() -> Path:
        """The per-user settings file. Dev uses its own name so running from source never edits an
        installed app's settings."""
        name = "settings.dev.yaml" if Environment.is_dev else "settings.yaml"
        return Environment.user_data_dir() / name

    @staticmethod
    def log_path() -> Path:
        """The active JSONL log file; rotated backups sit beside it. Dev keeps logs in the repo
        (gitignored) so they never mix with an installed app's."""
        directory = (
            Environment.resource_root() / "logs"
            if Environment.is_dev
            else Environment.user_data_dir() / "logs"
        )
        return directory / f"{executable_name()}.jsonl"
