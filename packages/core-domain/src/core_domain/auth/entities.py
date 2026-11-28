import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Self
from uuid import NAMESPACE_URL, uuid5

from core_domain.ddd import Entity, RuleViolation
from core_domain.ids import SessionId, UserId

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
        _require_expiry_fits(role, expires_at, now, "created")
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

    def can_sign_in(self) -> bool:
        return self.status is UserStatus.ACTIVE

    def can_suspend(self) -> bool:
        return self.status is UserStatus.ACTIVE

    def suspend(self, now: datetime) -> None:
        """Blocks an active user from signing in."""
        if not self.can_suspend():
            raise RuleViolation(f"A {self.status.name} user cannot be suspended")
        self.status = UserStatus.SUSPENDED
        self.updated_at = now

    def can_activate(self) -> bool:
        return self.status in (UserStatus.SUSPENDED, UserStatus.DELETED)

    def activate(self, now: datetime) -> None:
        """Lets a suspended or deleted user sign in again."""
        if not self.can_activate():
            raise RuleViolation(f"An {self.status.name} user cannot be activated")
        self.status = UserStatus.ACTIVE
        self.deleted_at = None
        self.updated_at = now

    def can_delete(self) -> bool:
        return self.status in (UserStatus.ACTIVE, UserStatus.SUSPENDED)

    def delete(self, now: datetime) -> None:
        """Soft deletes the user. They are kept so their history still resolves."""
        if not self.can_delete():
            raise RuleViolation(f"A {self.status.name} user cannot be deleted")
        self.status = UserStatus.DELETED
        self.deleted_at = now
        self.updated_at = now

    def can_change_role(self, role: UserRole, expires_at: datetime | None) -> bool:
        """False when nothing would change. A guest can be made a guest again with a new expiry."""
        if role is not self.role:
            return True
        return role is UserRole.GUEST and expires_at != self.expires_at

    def change_role(self, role: UserRole, expires_at: datetime | None, now: datetime) -> None:
        """Gives the user a new role. A guest's access must end at a time still to come; every
        other role's access does not expire, so leaving guest clears the expiry."""
        if not self.can_change_role(role, expires_at):
            raise RuleViolation(f"This user is already a {role.name} user")
        _require_expiry_fits(role, expires_at, now, "made")
        self.role = role
        self.expires_at = expires_at
        self.updated_at = now


@dataclass(eq=False)
class Session(Entity[SessionId]):
    """A person's sign-in at the identity provider, as a client knows it. The tokens behind it
    stay with the infrastructure that holds them and are never part of the entity."""

    id: SessionId
    email: str
    first_name: str
    last_name: str

    @classmethod
    def from_provider(
        cls,
        issuer: str,
        provider_session: str,
        email: str,
        first_name: str,
        last_name: str,
    ) -> Self:
        """The session the provider reported, with its email and names held to the same rules as
        a User's. The provider's own session ID need not be a UUID, so the ID is derived from it
        with the issuer: the same provider session always gets the same ID, and two providers'
        sessions never share one."""
        if not provider_session.strip():
            raise RuleViolation("A session cannot be created without the provider's session ID")
        email = _valid_email(email)
        _require_name_length("first name", first_name)
        _require_name_length("last name", last_name)
        session_id = SessionId(uuid5(NAMESPACE_URL, f"{issuer}#{provider_session}"))
        return cls(session_id, email, first_name, last_name)


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


def _require_expiry_fits(
    role: UserRole, expires_at: datetime | None, now: datetime, action: str
) -> None:
    """A guest's access must end at a time still to come; no other role's access expires."""
    if role is UserRole.GUEST:
        if expires_at is None:
            raise RuleViolation(f"A guest cannot be {action} without an expiry")
        if expires_at <= now:
            raise RuleViolation(f"A guest cannot be {action} with an expiry that has passed")
    elif expires_at is not None:
        raise RuleViolation(f"A {role.name} user cannot have an expiry")


def _require_name_length(label: str, name: str) -> None:
    if len(name) > MAX_NAME_LENGTH:
        raise RuleViolation(f"A {label} cannot be longer than {MAX_NAME_LENGTH} characters")
