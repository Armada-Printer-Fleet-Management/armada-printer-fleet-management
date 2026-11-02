"""The application's own logs: a test entry for checking logging by hand, and a zip for a user to
send to developers. Logging is runtime infrastructure rather than a domain, so this module takes
the archive directly."""

import logging
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from google.protobuf.empty_pb2 import Empty
from proto_utils.gen.common.v1.log_export_pb2 import LogExport

from armada_ipc._base import IpcModule, proto_response
from armada_runtime.log_archive import LogArchive

logger = logging.getLogger(__name__)

type ChooseSavePath = Callable[[str], Path | None]
"""Asks the user where to save a file, given a suggested name. None means they cancelled."""


class LogsIpc(IpcModule):
    def __init__(
        self, archive: LogArchive, choose_save_path: ChooseSavePath, filename_prefix: str
    ) -> None:
        self._archive = archive
        self._choose_save_path = choose_save_path
        self._filename_prefix = filename_prefix

    @proto_response
    def write_test_log(self) -> Empty:
        logger.info("Test log entry from the Settings page", extra={"source": "test_button"})
        return Empty()

    @proto_response
    def export_logs(self) -> LogExport:
        suggested = f"{self._filename_prefix}-logs-{datetime.now():%Y%m%d-%H%M%S}.zip"
        destination = self._choose_save_path(suggested)
        if destination is None:
            return LogExport(cancelled=True)
        logger.info("Exporting logs", extra={"file_count": len(self._archive.log_files())})
        return LogExport(path=str(self._archive.write(destination)))
