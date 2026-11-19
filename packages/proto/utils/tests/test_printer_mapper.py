from datetime import UTC, datetime

import pytest
from core_domain.fleet import Printer, PrinterCapabilities, PrinterStatus, PrinterType
from core_domain.ids import PrinterId, PrintJobId

from proto_utils.gen.fleet.v1 import printer_pb2, printer_type_pb2
from proto_utils.mappers import PrinterMapper, PrinterTypeMapper

TIME = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)
CAPABILITIES = PrinterCapabilities(250, 210, 220, 0.4, 1.75)


def every_field_set() -> Printer:
    return Printer(
        id=PrinterId.new(),
        name="Printer 1",
        model="Model",
        capabilities=CAPABILITIES,
        status=PrinterStatus.PRINTING,
        created_at=TIME,
        updated_at=TIME,
        print_job_id=PrintJobId.new(),
        progress_percent=50,
    )


def test_to_proto_maps_every_field_of_the_message() -> None:
    """Fails when a field is added to fleet.v1.Printer without being mapped."""
    message = PrinterMapper().to_proto(every_field_set())
    mapped = {field.name for field, _ in message.ListFields()}
    assert mapped == {field.name for field in printer_pb2.Printer.DESCRIPTOR.fields}


def test_to_entity_reverses_to_proto() -> None:
    printer = every_field_set()
    round_tripped = PrinterMapper().to_entity(PrinterMapper().to_proto(printer))
    assert vars(round_tripped) == vars(printer)


def test_to_proto_carries_each_capability() -> None:
    capabilities = PrinterMapper().to_proto(every_field_set()).capabilities
    assert (
        capabilities.build_volume_x_mm,
        capabilities.build_volume_y_mm,
        capabilities.build_volume_z_mm,
        capabilities.nozzle_diameter_mm,
        capabilities.filament_diameter_mm,
    ) == (250, 210, 220, 0.4, 1.75)


@pytest.mark.parametrize("status", list(PrinterStatus))
def test_every_status_round_trips(status: PrinterStatus) -> None:
    printer = every_field_set()
    printer.status = status
    assert PrinterMapper().to_entity(PrinterMapper().to_proto(printer)).status is status


def test_to_entity_rejects_an_unspecified_status() -> None:
    message = PrinterMapper().to_proto(every_field_set())
    message.status = printer_pb2.PRINTER_STATUS_UNSPECIFIED
    with pytest.raises(ValueError):
        PrinterMapper().to_entity(message)


def test_printer_type_maps_every_field_of_the_message() -> None:
    """Fails when a field is added to fleet.v1.PrinterType without being mapped."""
    message = PrinterTypeMapper().to_proto(PrinterType("Model", CAPABILITIES))
    mapped = {field.name for field, _ in message.ListFields()}
    assert mapped == {field.name for field in printer_type_pb2.PrinterType.DESCRIPTOR.fields}


def test_printer_type_round_trips() -> None:
    printer_type = PrinterType("Model", CAPABILITIES)
    round_tripped = PrinterTypeMapper().to_entity(PrinterTypeMapper().to_proto(printer_type))
    assert round_tripped == printer_type
