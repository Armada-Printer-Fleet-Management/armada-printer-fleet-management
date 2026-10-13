import re
from collections.abc import Callable, Generator
from contextlib import contextmanager
from uuid import UUID

import structlog
from connectrpc.code import Code
from connectrpc.errors import ConnectError
from core_domain.ddd import EntityNotFound, RuleViolation
from plugin_api.file_store import FileStoreError, StoredFileNotFoundError
from proto_utils import ProtoId, ProtoMapper

logger = structlog.stdlib.get_logger(__name__)


@contextmanager
def domain_errors_as_connect() -> Generator[None]:
    """Reports the domain's deliberate errors, and outages of the plugins behind it, to Connect
    clients with the matching code. Every RPC handler wraps its domain calls in this, so each error
    means the same thing on every RPC.

    A missing stored file is not mapped: the domain service that asked for it knows which entity
    is missing and raises EntityNotFound instead, so one arriving here is a bug."""
    try:
        yield
    except EntityNotFound as error:
        raise ConnectError(Code.NOT_FOUND, str(error)) from error
    except RuleViolation as error:
        raise ConnectError(Code.FAILED_PRECONDITION, str(error)) from error
    except StoredFileNotFoundError:
        raise
    except FileStoreError as error:
        # Logged, not reported: the message can carry internal details such as hostnames.
        logger.warning("file store failed", exc_info=error)
        raise ConnectError(Code.UNAVAILABLE, "file storage is unavailable") from error


def request_id[IdT](id_type: Callable[[UUID], IdT], message: ProtoId) -> IdT:
    """Reads a required typed ID from a request, rejecting a missing or malformed one. The contract
    names every ID field after its type, so PrintJobId is always the field print_job_id."""
    try:
        return ProtoMapper.id_from_proto(id_type, message)
    except ValueError as error:
        field_name = re.sub(r"(?<!^)(?=[A-Z])", "_", type(message).__name__).lower()
        raise ConnectError(Code.INVALID_ARGUMENT, f"{field_name} must be a UUID") from error
