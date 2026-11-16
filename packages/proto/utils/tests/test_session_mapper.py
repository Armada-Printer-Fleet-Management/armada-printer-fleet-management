from core_domain.auth import Session
from core_domain.ids import SessionId

from proto_utils.mappers import SessionMapper


def session(first_name: str = "First", last_name: str = "Last") -> Session:
    return Session(
        id=SessionId.new(),
        email="operator@example.com",
        first_name=first_name,
        last_name=last_name,
    )


def test_to_entity_reverses_to_proto() -> None:
    original = session()

    assert vars(SessionMapper().to_entity(SessionMapper().to_proto(original))) == vars(original)


def test_to_proto_puts_each_field_on_the_wire() -> None:
    original = session()

    message = SessionMapper().to_proto(original)

    assert message.id.value == str(original.id)
    assert (message.email, message.first_name, message.last_name) == (
        "operator@example.com",
        "First",
        "Last",
    )


def test_empty_names_map_both_ways() -> None:
    original = session(first_name="", last_name="")

    message = SessionMapper().to_proto(original)

    assert (message.first_name, message.last_name) == ("", "")
    assert vars(SessionMapper().to_entity(message)) == vars(original)
