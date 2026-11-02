import json
import logging
import zipfile
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

MANIFEST_NAME = "manifest.json"


class LogArchive:
    """Bundles the log directory into one zip for a user to send to developers. The manifest says
    which build and system wrote the logs, since the logs themselves do not."""

    def __init__(self, log_dir: Path, manifest: Mapping[str, str]) -> None:
        self._log_dir = log_dir
        self._manifest = manifest

    def log_files(self) -> list[Path]:
        """The active file and its rotated backups: `x.jsonl`, `x.jsonl.1`, and so on."""
        if not self._log_dir.is_dir():
            return []
        return sorted(path for path in self._log_dir.glob("*.jsonl*") if path.is_file())

    def write(self, destination: Path) -> Path:
        # Records still buffered in a handler would otherwise be missing from the zip.
        for handler in logging.getLogger().handlers:
            handler.flush()
        with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            manifest = {**self._manifest, "exported_at": datetime.now(UTC).isoformat()}
            archive.writestr(MANIFEST_NAME, json.dumps(manifest, indent=2))
            for path in self.log_files():
                archive.write(path, arcname=path.name)
        return destination
