from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import pytest

from core_domain.auth import User, UserRole, UserStatus
from core_domain.auth.entities import MAX_EMAIL_LENGTH, MAX_NAME_LENGTH
from core_domain.ddd import RuleViolation

NOW = datetime(2026, 10, 1, tzinfo=UTC)
LATER = NOW + timedelta(days=1)


def create(
    *,
    identity_provider_ref: str = "identity-provider-ref",
    email: str = "user@example.com",
    role: UserRole = UserRole.STUDENT,
    expires_at: datetime | None = None,
    first_name: str = "First",
    last_name: str = "Last",
) -> User:
    return User.create(identity_provider_ref, email, first_name, last_name, role, expires_at, NOW)


def test_create_makes_an_active_user_with_no_history() -> None:
    user = create()

    assert user.status is UserStatus.ACTIVE
    assert user.role is UserRole.STUDENT
    assert (user.created_at, user.updated_at) == (NOW, NOW)
    assert (user.expires_at, user.last_login_at, user.deleted_at) == (None, None, None)


def test_create_gives_each_user_a_new_id() -> None:
    assert create().id != create().id


def test_create_trims_and_lower_cases_the_email() -> None:
    assert create(email="  User@Example.COM ").email == "user@example.com"


@pytest.mark.parametrize("email", ["", "   "])
def test_create_refuses_a_blank_email(email: str) -> None:
    with pytest.raises(RuleViolation):
        create(email=email)


@pytest.mark.parametrize("identity_provider_ref", ["", "   "])
def test_create_refuses_a_blank_identity_provider_ref(identity_provider_ref: str) -> None:
    with pytest.raises(RuleViolation):
        create(identity_provider_ref=identity_provider_ref)


def test_create_accepts_a_guest_whose_access_ends_later() -> None:
    user = create(role=UserRole.GUEST, expires_at=LATER)
    assert user.expires_at == LATER


@pytest.mark.parametrize(
    "expires_at", [None, NOW, NOW - timedelta(seconds=1)], ids=["none", "now", "past"]
)
def test_create_refuses_a_guest_without_a_future_expiry(expires_at: datetime | None) -> None:
    with pytest.raises(RuleViolation):
        create(role=UserRole.GUEST, expires_at=expires_at)


@pytest.mark.parametrize("role", [r for r in UserRole if r is not UserRole.GUEST])
def test_create_refuses_an_expiry_for_any_other_role(role: UserRole) -> None:
    with pytest.raises(RuleViolation):
        create(role=role, expires_at=LATER)


@pytest.mark.parametrize(
    "email",
    [
        "user@example.com",
        "user@mail.example.com",
        "user+tag@example.com",
        "first.last@example.com",
    ],
)
def test_create_accepts_a_well_formed_email(email: str) -> None:
    assert create(email=email).email == email


@pytest.mark.parametrize(
    "email",
    [
        pytest.param("user.example.com", id="no-at"),
        pytest.param("@example.com", id="nothing-before-at"),
        pytest.param("user@", id="no-domain"),
        pytest.param("user@example", id="domain-without-dot"),
        pytest.param("user@@example.com", id="two-ats-together"),
        pytest.param("user@mail@example.com", id="two-ats-apart"),
        pytest.param("first last@example.com", id="space"),
        pytest.param("first\tlast@example.com", id="tab"),
        pytest.param("user@.example.com", id="domain-starts-with-dot"),
        pytest.param("user@example.com.", id="domain-ends-with-dot"),
        pytest.param("user@example..com", id="two-dots-in-a-row"),
    ],
)
def test_create_refuses_a_malformed_email(email: str) -> None:
    with pytest.raises(RuleViolation):
        create(email=email)


def email_of_length(length: int) -> str:
    domain = "@example.com"
    return "x" * (length - len(domain)) + domain


def test_create_accepts_an_email_at_the_length_limit() -> None:
    assert len(create(email=email_of_length(MAX_EMAIL_LENGTH)).email) == MAX_EMAIL_LENGTH


def test_create_refuses_an_email_over_the_length_limit() -> None:
    with pytest.raises(RuleViolation):
        create(email=email_of_length(MAX_EMAIL_LENGTH + 1))


def test_create_accepts_names_at_the_length_limit() -> None:
    name = "x" * MAX_NAME_LENGTH
    user = create(first_name=name, last_name=name)
    assert (user.first_name, user.last_name) == (name, name)


def test_create_refuses_a_first_name_over_the_length_limit() -> None:
    with pytest.raises(RuleViolation):
        create(first_name="x" * (MAX_NAME_LENGTH + 1))


def test_create_refuses_a_last_name_over_the_length_limit() -> None:
    with pytest.raises(RuleViolation):
        create(last_name="x" * (MAX_NAME_LENGTH + 1))


# Checking a new user before their account exists


def test_check_new_returns_the_email_trimmed_and_lower_cased() -> None:
    email = User.check_new("  User@Example.COM ", "First", "Last", UserRole.STUDENT, None, NOW)

    assert email == "user@example.com"


@pytest.mark.parametrize(
    ("email", "first_name", "last_name", "role", "expires_at"),
    [
        ("", "First", "Last", UserRole.STUDENT, None),
        ("not-an-email", "First", "Last", UserRole.STUDENT, None),
        ("a" * MAX_EMAIL_LENGTH + "@example.com", "First", "Last", UserRole.STUDENT, None),
        ("user@example.com", "a" * (MAX_NAME_LENGTH + 1), "Last", UserRole.STUDENT, None),
        ("user@example.com", "First", "a" * (MAX_NAME_LENGTH + 1), UserRole.STUDENT, None),
        ("user@example.com", "First", "Last", UserRole.GUEST, None),
        ("user@example.com", "First", "Last", UserRole.GUEST, NOW),
        ("user@example.com", "First", "Last", UserRole.STUDENT, LATER),
    ],
    ids=[
        "blank email",
        "malformed email",
        "email too long",
        "first name too long",
        "last name too long",
        "guest without expiry",
        "guest expiry not in the future",
        "expiry for another role",
    ],
)
def test_check_new_refuses_what_create_refuses(
    email: str, first_name: str, last_name: str, role: UserRole, expires_at: datetime | None
) -> None:
    with pytest.raises(RuleViolation):
        User.check_new(email, first_name, last_name, role, expires_at, NOW)


# Status transitions


def in_status(status: UserStatus) -> User:
    user = create()
    user.status = status
    if status is UserStatus.DELETED:
        user.deleted_at = NOW
    return user


@pytest.mark.parametrize("status", list(UserStatus))
def test_only_an_active_user_can_sign_in(status: UserStatus) -> None:
    assert in_status(status).can_sign_in() is (status is UserStatus.ACTIVE)


def test_suspend_moves_an_active_user_to_suspended() -> None:
    user = in_status(UserStatus.ACTIVE)

    user.suspend(LATER)

    assert user.status is UserStatus.SUSPENDED
    assert (user.updated_at, user.deleted_at) == (LATER, None)


@pytest.mark.parametrize("status", [UserStatus.ACTIVE, UserStatus.SUSPENDED])
def test_delete_moves_a_user_to_deleted_and_records_when(status: UserStatus) -> None:
    user = in_status(status)

    user.delete(LATER)

    assert user.status is UserStatus.DELETED
    assert (user.updated_at, user.deleted_at) == (LATER, LATER)


@pytest.mark.parametrize("status", [UserStatus.SUSPENDED, UserStatus.DELETED])
def test_activate_moves_a_user_to_active_and_clears_deleted_at(status: UserStatus) -> None:
    user = in_status(status)

    user.activate(LATER)

    assert user.status is UserStatus.ACTIVE
    assert (user.updated_at, user.deleted_at) == (LATER, None)


@pytest.mark.parametrize(
    ("transition", "status"),
    [
        (User.suspend, UserStatus.SUSPENDED),
        (User.suspend, UserStatus.DELETED),
        (User.activate, UserStatus.ACTIVE),
        (User.delete, UserStatus.DELETED),
    ],
    ids=["suspend suspended", "suspend deleted", "activate active", "delete deleted"],
)
def test_a_refused_transition_changes_nothing(
    transition: Callable[[User, datetime], None], status: UserStatus
) -> None:
    user = in_status(status)
    before = (user.status, user.updated_at, user.deleted_at)

    with pytest.raises(RuleViolation):
        transition(user, LATER)

    assert (user.status, user.updated_at, user.deleted_at) == before


@pytest.mark.parametrize("status", list(UserStatus))
@pytest.mark.parametrize(
    ("hint", "transition"),
    [
        (User.can_suspend, User.suspend),
        (User.can_activate, User.activate),
        (User.can_delete, User.delete),
    ],
    ids=["suspend", "activate", "delete"],
)
def test_each_hint_agrees_with_its_rule(
    hint: Callable[[User], bool],
    transition: Callable[[User, datetime], None],
    status: UserStatus,
) -> None:
    user = in_status(status)
    allowed = hint(user)

    try:
        transition(user, LATER)
        refused = False
    except RuleViolation:
        refused = True

    assert allowed is not refused


# Role changes


def as_guest(expires_at: datetime = LATER) -> User:
    return create(role=UserRole.GUEST, expires_at=expires_at)


def test_change_role_gives_the_user_the_new_role() -> None:
    user = create(role=UserRole.STUDENT)

    user.change_role(UserRole.STAFF, None, LATER)

    assert user.role is UserRole.STAFF
    assert (user.expires_at, user.updated_at) == (None, LATER)


@pytest.mark.parametrize("role", [r for r in UserRole if r is not UserRole.GUEST])
def test_change_role_refuses_the_role_the_user_already_has(role: UserRole) -> None:
    user = create(role=role)

    with pytest.raises(RuleViolation):
        user.change_role(role, None, LATER)

    assert (user.role, user.updated_at) == (role, NOW)


def test_change_role_refuses_a_guest_the_same_expiry() -> None:
    user = as_guest()

    with pytest.raises(RuleViolation):
        user.change_role(UserRole.GUEST, LATER, NOW)

    assert (user.expires_at, user.updated_at) == (LATER, NOW)


def test_change_role_makes_a_user_a_guest_until_a_future_expiry() -> None:
    user = create(role=UserRole.STUDENT)

    user.change_role(UserRole.GUEST, LATER, NOW)

    assert (user.role, user.expires_at) == (UserRole.GUEST, LATER)


def test_change_role_gives_a_guest_a_new_expiry() -> None:
    user = as_guest()
    new_expiry = LATER + timedelta(days=7)

    user.change_role(UserRole.GUEST, new_expiry, NOW)

    assert (user.role, user.expires_at) == (UserRole.GUEST, new_expiry)


@pytest.mark.parametrize(
    "expires_at", [None, NOW, NOW - timedelta(seconds=1)], ids=["none", "now", "past"]
)
def test_change_role_refuses_a_guest_without_a_future_expiry(expires_at: datetime | None) -> None:
    user = create(role=UserRole.STUDENT)

    with pytest.raises(RuleViolation):
        user.change_role(UserRole.GUEST, expires_at, NOW)

    assert (user.role, user.expires_at) == (UserRole.STUDENT, None)


@pytest.mark.parametrize("role", [r for r in UserRole if r is not UserRole.GUEST])
def test_leaving_guest_clears_the_expiry(role: UserRole) -> None:
    user = as_guest()

    user.change_role(role, None, NOW)

    assert (user.role, user.expires_at) == (role, None)


@pytest.mark.parametrize("role", [r for r in UserRole if r is not UserRole.GUEST])
def test_change_role_refuses_an_expiry_for_any_other_role(role: UserRole) -> None:
    user = as_guest()

    with pytest.raises(RuleViolation):
        user.change_role(role, LATER, NOW)

    assert (user.role, user.expires_at) == (UserRole.GUEST, LATER)
