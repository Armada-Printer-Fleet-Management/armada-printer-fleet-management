"""The session IPC calls, with the session service mocked."""

from unittest.mock import create_autospec

from core_domain.auth import Session

from armada_domains.auth.service import SessionService
from armada_ipc.session import SessionIpc

OPERATOR = Session.from_provider(
    "https://idp.example/realms/armada",
    "provider-session-1",
    "operator@example.edu",
    "An",
    "Operator",
)
SIGNED_IN_JSON = {
    "session": {
        "id": {"value": str(OPERATOR.id)},
        "email": "operator@example.edu",
        "firstName": "An",
        "lastName": "Operator",
    }
}
SIGNED_OUT_JSON: dict[str, object] = {}


def test_sign_in_returns_the_session_as_protobuf_json() -> None:
    service = create_autospec(SessionService, instance=True)
    service.sign_in.return_value = OPERATOR

    assert SessionIpc(service).sign_in() == SIGNED_IN_JSON


def test_session_returns_the_current_session_as_protobuf_json() -> None:
    service = create_autospec(SessionService, instance=True)
    service.session.return_value = OPERATOR

    assert SessionIpc(service).session() == SIGNED_IN_JSON


def test_sign_out_returns_no_session() -> None:
    service = create_autospec(SessionService, instance=True)

    assert SessionIpc(service).sign_out() == SIGNED_OUT_JSON
    service.sign_out.assert_called_once()
