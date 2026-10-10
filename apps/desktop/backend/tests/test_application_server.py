"""The application server print job adapter and the print job IPC call, with the Connect client
mocked."""

from collections.abc import Iterator
from datetime import UTC, datetime
from unittest.mock import MagicMock, create_autospec, patch

import pytest
from connectrpc.code import Code
from connectrpc.errors import ConnectError
from core_domain.ddd import EntityNotFound
from core_domain.ids import PrintJobId, UserId
from core_domain.print_job import PrintJob, PrintJobStatus
from proto_utils.gen.server.v1.print_job_service_pb2 import GetPrintJobResponse
from proto_utils.mappers import PrintJobMapper

from armada_domains.print_job.service import PrintJobService
from armada_infrastructure.application_server.print_job import ApplicationServerPrintJobs
from armada_ipc.print_job import PrintJobIpc

TIME = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)
KNOWN = PrintJob(PrintJobId.new(), UserId.new(), PrintJobStatus.SUBMITTED, TIME, TIME, "notes")


@pytest.fixture
def client() -> Iterator[MagicMock]:
    """The PrintJobServiceClientSync the adapter builds, replaced by a mock."""
    target = "armada_infrastructure.application_server.print_job.PrintJobServiceClientSync"
    with patch(target) as client_type:
        yield client_type.return_value


@pytest.fixture
def print_jobs(client: MagicMock) -> ApplicationServerPrintJobs:
    return ApplicationServerPrintJobs(MagicMock())


def test_get_returns_the_server_job_as_an_entity(
    client: MagicMock, print_jobs: ApplicationServerPrintJobs
) -> None:
    client.get_print_job.return_value = GetPrintJobResponse(
        print_job=PrintJobMapper().to_proto(KNOWN)
    )

    assert vars(print_jobs.get(KNOWN.id)) == vars(KNOWN)
    request = client.get_print_job.call_args.args[0]
    assert request.print_job_id.value == str(KNOWN.id)


def test_get_turns_not_found_into_entity_not_found(
    client: MagicMock, print_jobs: ApplicationServerPrintJobs
) -> None:
    client.get_print_job.side_effect = ConnectError(Code.NOT_FOUND, "no such print job")

    with pytest.raises(EntityNotFound):
        print_jobs.get(KNOWN.id)


def test_get_passes_other_connect_errors_through(
    client: MagicMock, print_jobs: ApplicationServerPrintJobs
) -> None:
    client.get_print_job.side_effect = ConnectError(Code.UNAVAILABLE, "server down")

    with pytest.raises(ConnectError):
        print_jobs.get(KNOWN.id)


def test_ipc_returns_the_print_job_as_protobuf_json() -> None:
    service = create_autospec(PrintJobService, instance=True)
    service.print_job.return_value = KNOWN

    reply = PrintJobIpc(service).print_job({"printJobId": {"value": str(KNOWN.id)}})

    service.print_job.assert_called_once_with(KNOWN.id)
    print_job = reply["printJob"]
    assert isinstance(print_job, dict) and print_job["status"] == "PRINT_JOB_STATUS_SUBMITTED"
