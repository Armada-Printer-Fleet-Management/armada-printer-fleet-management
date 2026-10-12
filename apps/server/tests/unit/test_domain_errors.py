import pytest
from connectrpc.code import Code
from connectrpc.errors import ConnectError
from core_domain.ddd import EntityNotFound, RuleViolation, Unavailable
from core_domain.ids import PrintJobId
from proto_utils.gen.id.v1.print_job_id_pb2 import PrintJobId as PrintJobIdMessage

from api.services.domain_errors import domain_errors_as_connect, request_id


def raised_code(error: Exception) -> Code:
    with pytest.raises(ConnectError) as raised, domain_errors_as_connect():
        raise error
    return raised.value.code


def test_a_missing_entity_is_not_found() -> None:
    assert raised_code(EntityNotFound(PrintJobId.new())) is Code.NOT_FOUND


def test_a_refused_rule_is_a_failed_precondition() -> None:
    assert raised_code(RuleViolation("no")) is Code.FAILED_PRECONDITION


def test_an_unavailable_dependency_is_unavailable_without_its_cause() -> None:
    with pytest.raises(ConnectError) as raised, domain_errors_as_connect():
        raise Unavailable("file storage") from OSError("localhost:3900 refused")

    assert raised.value.code is Code.UNAVAILABLE
    assert raised.value.message == "file storage is unavailable"


def test_a_malformed_id_is_an_invalid_argument() -> None:
    with pytest.raises(ConnectError) as raised:
        request_id(PrintJobId, PrintJobIdMessage(value="not-a-uuid"))

    assert raised.value.code is Code.INVALID_ARGUMENT
    assert raised.value.message == "print_job_id must be a UUID"
