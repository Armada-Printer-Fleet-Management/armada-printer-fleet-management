import pytest

from core_domain.auth import Session
from core_domain.auth.entities import MAX_NAME_LENGTH
from core_domain.ddd import RuleViolation

ISSUER = "https://idp.example/realms/armada"


def from_provider(
    *,
    issuer: str = ISSUER,
    provider_session: str = "provider-session-1",
    email: str = "operator@example.com",
    first_name: str = "First",
    last_name: str = "Last",
) -> Session:
    return Session.from_provider(issuer, provider_session, email, first_name, last_name)


# The ID, from the provider's session


def test_the_same_provider_session_always_gets_the_same_id() -> None:
    assert from_provider().id == from_provider().id


def test_a_different_provider_session_gets_a_different_id() -> None:
    assert from_provider().id != from_provider(provider_session="provider-session-2").id


def test_the_same_provider_session_at_another_issuer_gets_a_different_id() -> None:
    other = from_provider(issuer="https://other-idp.example/realms/armada")
    assert from_provider().id != other.id


@pytest.mark.parametrize("provider_session", ["", "   "])
def test_a_blank_provider_session_is_refused(provider_session: str) -> None:
    with pytest.raises(RuleViolation):
        from_provider(provider_session=provider_session)


# Email


def test_the_email_is_trimmed_and_lower_cased() -> None:
    assert from_provider(email="  Operator@Example.COM ").email == "operator@example.com"


@pytest.mark.parametrize("email", ["", "   ", "operator", "operator@example", "a b@example.com"])
def test_a_blank_or_badly_shaped_email_is_refused(email: str) -> None:
    with pytest.raises(RuleViolation):
        from_provider(email=email)


# Names


def test_empty_names_are_allowed() -> None:
    session = from_provider(first_name="", last_name="")

    assert (session.first_name, session.last_name) == ("", "")


@pytest.mark.parametrize("name", ["first_name", "last_name"])
def test_a_name_over_the_length_limit_is_refused(name: str) -> None:
    with pytest.raises(RuleViolation):
        from_provider(**{name: "x" * (MAX_NAME_LENGTH + 1)})
