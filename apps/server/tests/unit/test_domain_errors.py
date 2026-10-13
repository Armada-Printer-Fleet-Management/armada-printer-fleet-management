import pytest
from connectrpc.code import Code
from connectrpc.errors import ConnectError
from core_domain.ddd import EntityNotFound, RuleViolation
from core_domain.ids import PrintJobId
from plugin_api.file_store import FileStoreError, StoredFileNotFoundError
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


def test_a_file_store_outage_is_unavailable_without_its_details() -> None:
    with pytest.raises(ConnectError) as raised, domain_errors_as_connect():
        raise FileStoreError("store.internal:3900 refused the connection")

    assert raised.value.code is Code.UNAVAILABLE
    assert "store.internal" not in raised.value.message


def test_a_missing_stored_file_is_left_for_the_domain_to_translate() -> None:
    with pytest.raises(StoredFileNotFoundError), domain_errors_as_connect():
        raise StoredFileNotFoundError("key")


def test_a_malformed_id_is_an_invalid_argument() -> None:
    with pytest.raises(ConnectError) as raised:
        request_id(PrintJobId, PrintJobIdMessage(value="not-a-uuid"))

    assert raised.value.code is Code.INVALID_ARGUMENT
    assert raised.value.message == "print_job_id must be a UUID"
