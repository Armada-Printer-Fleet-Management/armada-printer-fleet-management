import logging.config
import os
from typing import Literal

import structlog
from structlog.typing import Processor

LogFormat = Literal["console", "json"]

# Run on every entry, from structlog loggers and from stdlib ones such as uvicorn's alike.
# Add custom processors here.
SHARED_PROCESSORS: list[Processor] = [
    structlog.contextvars.merge_contextvars,
    structlog.stdlib.add_log_level,
    structlog.stdlib.add_logger_name,
    structlog.processors.TimeStamper(fmt="iso", utc=True),
    structlog.processors.StackInfoRenderer(),
]


def log_format() -> LogFormat:
    # Defaults to json so a deployment that sets nothing never gets development output.
    match os.environ.get("LOG_FORMAT", "json"):
        case "console":
            return "console"
        case "json":
            return "json"
        case other:
            raise ValueError(f"LOG_FORMAT must be 'console' or 'json', not {other!r}")


def _renderers(log_format: LogFormat) -> list[Processor]:
    if log_format == "console":
        return [structlog.dev.ConsoleRenderer()]
    return [structlog.processors.dict_tracebacks, structlog.processors.JSONRenderer()]


def logging_config(log_format: LogFormat) -> dict[str, object]:
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "structlog": {
                "()": structlog.stdlib.ProcessorFormatter,
                "foreign_pre_chain": SHARED_PROCESSORS,
                "processors": [
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    *_renderers(log_format),
                ],
            },
        },
        "handlers": {
            "stderr": {"class": "logging.StreamHandler", "formatter": "structlog"},
        },
        "root": {"handlers": ["stderr"], "level": "INFO"},
        "loggers": {
            # Clearing handlers so we don't get duplicate logs
            "uvicorn": {"handlers": [], "propagate": True},
            "uvicorn.error": {"handlers": [], "propagate": True},
            "uvicorn.access": {"handlers": [], "propagate": False},
        },
    }


def configure_logging() -> None:
    logging.config.dictConfig(logging_config(log_format()))
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            *SHARED_PROCESSORS,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        # Caching would stop structlog.testing.capture_logs() from seeing loggers already used.
        cache_logger_on_first_use=False,
    )
