from datetime import UTC, datetime

from core_domain.ids import PrinterQueueId
from core_domain.printer_queue import PrinterQueue

from proto_utils.gen.printer_queue.v1 import printer_queue_pb2
from proto_utils.mappers import PrinterQueueMapper

TIME = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)


def every_field_set() -> PrinterQueue:
    return PrinterQueue(PrinterQueueId.new(), "General", True, TIME, TIME)


def test_to_proto_maps_every_field_of_the_message() -> None:
    """Fails when a field is added to printer_queue.v1.PrinterQueue without being mapped."""
    message = PrinterQueueMapper().to_proto(every_field_set())
    mapped = {field.name for field, _ in message.ListFields()}
    assert mapped == {field.name for field in printer_queue_pb2.PrinterQueue.DESCRIPTOR.fields}


def test_to_entity_reverses_to_proto() -> None:
    printer_queue = every_field_set()
    round_tripped = PrinterQueueMapper().to_entity(PrinterQueueMapper().to_proto(printer_queue))
    assert vars(round_tripped) == vars(printer_queue)
