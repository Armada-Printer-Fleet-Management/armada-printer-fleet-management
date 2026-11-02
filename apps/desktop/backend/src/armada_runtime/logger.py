import json
import logging
import sys
import threading
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from types import TracebackType
from typing import TextIO

MAX_FILE_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 4
CONSOLE_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"

# Attributes every LogRecord has. Anything else on a record arrived through `extra=`.
_STANDARD_ATTRIBUTES = frozenset(logging.LogRecord("", 0, "", 0, "", None, None).__dict__) | {
    "message",
    "asctime",
    "taskName",
}


class JsonLinesFormatter(logging.Formatter):
    """One JSON object per record. Paths carry the user's name and these logs are sent to
    developers, so only the file name is kept, and the home folder in any text becomes `~`."""

    def __init__(self, home: Path | None = None) -> None:
        super().__init__()
        self._home = str(home or Path.home())

    def _without_home(self, text: str) -> str:
        return text.replace(self._home, "~")

    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": self._without_home(record.getMessage()),
            "module": record.module,
            "file": record.filename,
            "function": record.funcName,
            "line": record.lineno,
            "process": record.process,
            "thread": record.threadName,
        }
        if record.exc_info:
            entry["exception"] = self._without_home(self.formatException(record.exc_info))
        if record.stack_info:
            entry["stack"] = self._without_home(self.formatStack(record.stack_info))
        for key, value in record.__dict__.items():
            if key not in _STANDARD_ATTRIBUTES:
                entry[key] = value
        return json.dumps(entry, default=str, ensure_ascii=False)


class ApplicationLogger:
    """Routes every logger in the process to a rotating JSONL file, and to the console when the
    process has one. Install it once at startup; everywhere else uses
    `logging.getLogger(__name__)`, which keeps domains free of any import from this package."""

    def __init__(self, log_file: Path, level: int, console: TextIO | None = None) -> None:
        self._log_file = log_file
        self._level = level
        self._console = console

    def install(self) -> None:
        self._log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            self._log_file, maxBytes=MAX_FILE_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
        )
        file_handler.setFormatter(JsonLinesFormatter())

        root = logging.getLogger()
        root.setLevel(self._level)
        root.addHandler(file_handler)
        # A windowed (console=False) build has no stderr, so there is nothing to write to.
        if self._console is not None:
            console_handler = logging.StreamHandler(self._console)
            console_handler.setFormatter(logging.Formatter(CONSOLE_FORMAT))
            root.addHandler(console_handler)

        # pywebview attaches its own stderr handler on import; drop it so its records reach
        # the console once, through ours, instead of twice.
        logging.getLogger("pywebview").handlers.clear()

        self._capture_uncaught_exceptions()

    def _capture_uncaught_exceptions(self) -> None:
        log = logging.getLogger("uncaught")
        previous_hook = sys.excepthook
        previous_thread_hook = threading.excepthook

        def hook(
            kind: type[BaseException], error: BaseException, trace: TracebackType | None
        ) -> None:
            log.critical("Uncaught exception", exc_info=(kind, error, trace))
            previous_hook(kind, error, trace)

        def thread_hook(args: threading.ExceptHookArgs) -> None:
            if args.exc_value is not None:
                log.critical(
                    "Uncaught exception in thread %s",
                    args.thread.name if args.thread else "unknown",
                    exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
                )
            previous_thread_hook(args)

        sys.excepthook = hook
        threading.excepthook = thread_hook
