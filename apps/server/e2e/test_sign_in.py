"""As a student or member of staff, I sign in and the server accepts who I am, and allows only
what my role may do."""

import pytest
from connectrpc.code import Code
from connectrpc.errors import ConnectError
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


@pytest.mark.xfail(
    strict=True,
    reason="needs AUTH_ENFORCE on the target; until then a refusal is only logged",
)
def test_the_server_refuses_a_student_a_staff_only_call(as_student: SignedIn) -> None:
    with pytest.raises(ConnectError) as refused:
        as_student.printers.list_printers(ListPrintersRequest(page=PageRequest(page_size=1)))

    assert refused.value.code is Code.PERMISSION_DENIED
