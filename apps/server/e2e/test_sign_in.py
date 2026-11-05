"""As a student or member of staff, I sign in and the server accepts who I am."""

import pytest
from proto_utils.gen.common.v1.page_pb2 import PageRequest
from proto_utils.gen.server.v1.printer_service_pb2 import ListPrintersRequest

from e2e.auth import KeycloakTokens
from e2e.conftest import SignedIn
from e2e.settings import E2eRole


@pytest.mark.parametrize("role", list(E2eRole))
def test_each_test_user_can_sign_in(tokens: KeycloakTokens, role: E2eRole) -> None:
    assert tokens.token(role)


def test_the_server_accepts_a_signed_in_member_of_staff(as_staff: SignedIn) -> None:
    # The server rejects a token it cannot verify with a 401, so a reply proves it accepted one.
    as_staff.printers.list_printers(ListPrintersRequest(page=PageRequest(page_size=1)))
