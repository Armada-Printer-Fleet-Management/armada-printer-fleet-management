from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from enum import StrEnum


class Role(StrEnum):
    GUEST = "guest"
    STUDENT = "student"
    STAFF = "staff"
    ADMIN = "admin"


@dataclass(frozen=True)
class Caller:
    """Who made a request, as their verified access token says. The subject is the identity
    provider's ID for them, not a UserId."""

    subject: str
    roles: frozenset[Role]


class InvalidAccessToken(Exception):
    """The request's access token was rejected. Reported as 401."""


_caller: ContextVar[Caller | None] = ContextVar("caller", default=None)


def current_caller() -> Caller | None:
    """Who made the current request, or None when it carried no token."""
    return _caller.get()


@contextmanager
def authenticated_as(caller: Caller | None) -> Generator[None]:
    """Makes `caller` the current caller for the code run inside the block."""
    token = _caller.set(caller)
    try:
        yield
    finally:
        _caller.reset(token)
