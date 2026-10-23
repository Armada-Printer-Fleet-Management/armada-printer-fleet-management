from collections.abc import Generator
from contextlib import contextmanager

import structlog
from core_domain.ddd import EntityNotFound, InvalidValue, RuleViolation, Unavailable
from fastapi import HTTPException, status

logger = structlog.stdlib.get_logger(__name__)


@contextmanager
def domain_errors_as_http() -> Generator[None]:
    """Reports the domain's errors to REST clients with the matching status, as
    domain_errors_as_connect does for RPC clients."""
    try:
        yield
    except EntityNotFound as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except InvalidValue as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from error
    except RuleViolation as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except Unavailable as error:
        # Only the message is reported; the cause is logged because it can name internal hosts.
        logger.warning("dependency unavailable", exc_info=error)
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(error)) from error
