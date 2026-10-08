from datetime import UTC, datetime

import pytest
from core_domain.ids import FileId, PrinterId, PrintJobId, QueueId, UserId
from core_domain.print_job import PrintJob, PrintJobStatus

from proto_utils.gen.print_job.v1 import print_job_pb2
from proto_utils.mappers import PrintJobMapper

TIME = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)


def every_field_set() -> PrintJob:
    return PrintJob(
        id=PrintJobId.new(),
        user_id=UserId.new(),
        status=PrintJobStatus.ASSIGNED,
        created_at=TIME,
        updated_at=TIME,
        user_notes="notes",
        queue_id=QueueId.new(),
        file_id=FileId.new(),
        status_reason="reason",
        printer_id=PrinterId.new(),
    )


def test_to_proto_maps_every_field_of_the_message() -> None:
    """Fails when a field is added to print_job.v1.PrintJob without being mapped."""
    message = PrintJobMapper().to_proto(every_field_set())
    mapped = {field.name for field, _ in message.ListFields()}
    assert mapped == {field.name for field in print_job_pb2.PrintJob.DESCRIPTOR.fields}


def test_to_entity_reverses_to_proto() -> None:
    print_job = every_field_set()
    round_tripped = PrintJobMapper().to_entity(PrintJobMapper().to_proto(print_job))
    assert vars(round_tripped) == vars(print_job)


@pytest.mark.parametrize("status", list(PrintJobStatus))
def test_every_status_round_trips(status: PrintJobStatus) -> None:
    print_job = every_field_set()
    print_job.status = status
    assert PrintJobMapper().to_entity(PrintJobMapper().to_proto(print_job)).status is status


def test_to_entity_rejects_an_unspecified_status() -> None:
    message = PrintJobMapper().to_proto(every_field_set())
    message.status = print_job_pb2.PRINT_JOB_STATUS_UNSPECIFIED
    with pytest.raises(ValueError):
        PrintJobMapper().to_entity(message)
