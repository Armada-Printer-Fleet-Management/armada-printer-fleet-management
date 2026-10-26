from datetime import UTC, datetime

from core_domain.ids import PrinterId, PrintJobId
from core_domain.printer import Printer, PrinterStatus

from proto_utils.gen.printer.v1 import printer_pb2
from proto_utils.mappers import PrinterMapper

TIME = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)


def every_field_set() -> Printer:
    return Printer(
        id=PrinterId.new(),
        name="Printer 1",
        model="Model",
        status=PrinterStatus.PRINTING,
        created_at=TIME,
        updated_at=TIME,
        print_job_id=PrintJobId.new(),
        progress_percent=50,
    )


def test_to_proto_maps_every_field_of_the_message() -> None:
    """Fails when a field is added to printer.v1.Printer without being mapped."""
    message = PrinterMapper().to_proto(every_field_set())
    mapped = {field.name for field, _ in message.ListFields()}
    assert mapped == {field.name for field in printer_pb2.Printer.DESCRIPTOR.fields}


def test_to_entity_reverses_to_proto() -> None:
    printer = every_field_set()
    round_tripped = PrinterMapper().to_entity(PrinterMapper().to_proto(printer))
    assert vars(round_tripped) == vars(printer)
