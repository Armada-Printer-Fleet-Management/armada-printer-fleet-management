import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Self

from core_domain.ddd import Entity, RuleViolation
from core_domain.ids import UserId

MAX_NAME_LENGTH = 255
# The longest address the email standards allow.
MAX_EMAIL_LENGTH = 254
# One @, no whitespace, and a domain of dot-separated parts with none of them empty.
_EMAIL = re.compile(r"[^@\s]+@[^@\s.]+(?:\.[^@\s.]+)+")


class UserRole(Enum):
    """Mirrors auth.v1.UserRole, without UNSPECIFIED, which is never valid."""

    GUEST = auto()
    STUDENT = auto()
    STAFF = auto()
    ADMIN = auto()


class UserStatus(Enum):
    """Mirrors auth.v1.UserStatus, without UNSPECIFIED, which is never valid."""

    ACTIVE = auto()
    SUSPENDED = auto()
    DELETED = auto()


@dataclass(eq=False)
class User(Entity[UserId]):
    """A person who signs in to the system. Shared by every app; only the remote server persists
    a change to one, so on a client these rules are advisory.

    identity_provider_ref is the identity provider's ID for this person, the subject of their
    access token. It links a sign-in to this user and never leaves the server."""

    id: UserId
    identity_provider_ref: str
    email: str
    first_name: str
    last_name: str
    role: UserRole
    status: UserStatus
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None = None
    last_login_at: datetime | None = None
    deleted_at: datetime | None = None

    @staticmethod
    def check_new(
        email: str,
        first_name: str,
        last_name: str,
        role: UserRole,
        expires_at: datetime | None,
        now: datetime,
    ) -> str:
        """Checks a new user against every rule create applies apart from the identity provider
        reference, so a caller can refuse one before making their account there. Returns the email
        as it is stored: trimmed and lower-cased. A guest's access must end at a time still to
        come; every other role's access does not expire."""
        email = _valid_email(email)
        _require_name_length("first name", first_name)
        _require_name_length("last name", last_name)
        if role is UserRole.GUEST:
            if expires_at is None:
                raise RuleViolation("A guest cannot be created without an expiry")
            if expires_at <= now:
                raise RuleViolation("A guest cannot be created with an expiry that has passed")
        elif expires_at is not None:
            raise RuleViolation(f"A {role.name} user cannot have an expiry")
        return email

    @classmethod
    def create(
        cls,
        identity_provider_ref: str,
        email: str,
        first_name: str,
        last_name: str,
        role: UserRole,
        expires_at: datetime | None,
        now: datetime,
    ) -> Self:
        """A new, active user, refused as check_new refuses one, or without an identity provider
        reference."""
        if not identity_provider_ref.strip():
            raise RuleViolation("A user cannot be created without an identity provider reference")
        email = cls.check_new(email, first_name, last_name, role, expires_at, now)
        return cls(
            UserId.new(),
            identity_provider_ref,
            email,
            first_name,
            last_name,
            role,
            UserStatus.ACTIVE,
            now,
            now,
            expires_at,
        )


def _valid_email(email: str) -> str:
    """The email trimmed and lower-cased. Checks only its shape, since a full pattern refuses
    some real addresses and the identity provider verifies them."""
    email = email.strip().lower()
    if not email:
        raise RuleViolation("A user cannot be created without an email address")
    if len(email) > MAX_EMAIL_LENGTH:
        raise RuleViolation(f"An email address cannot be longer than {MAX_EMAIL_LENGTH} characters")
    if not _EMAIL.fullmatch(email):
        raise RuleViolation("That is not a valid email address")
    return email


def _require_name_length(label: str, name: str) -> None:
    if len(name) > MAX_NAME_LENGTH:
        raise RuleViolation(f"A {label} cannot be longer than {MAX_NAME_LENGTH} characters")
