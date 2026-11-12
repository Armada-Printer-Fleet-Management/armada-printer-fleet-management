import re
from datetime import UTC, datetime
from pathlib import Path

import pytest

from core_domain.ddd import RuleViolation
from core_domain.fleet import (
    Printer,
    PrinterCapabilities,
    PrinterStatus,
    PrinterType,
    printer_types,
)
from core_domain.ids import PrinterId, PrintJobId

PROTO = Path(__file__).resolve().parents[2] / "proto" / "fleet" / "v1" / "printer.proto"
CREATED = datetime(2026, 10, 1, tzinfo=UTC)
LATER = datetime(2026, 10, 2, tzinfo=UTC)


def test_status_mirrors_the_proto_enum() -> None:
    """Read as text, because core-domain may not depend on protobuf."""
    proto_values = re.findall(r"^\s*PRINTER_STATUS_(\w+)\s*=", PROTO.read_text(), re.MULTILINE)
    assert [v for v in proto_values if v != "UNSPECIFIED"] == [s.name for s in PrinterStatus]


def printer(status: PrinterStatus) -> Printer:
    return Printer(
        id=PrinterId.new(),
        name="Printer",
        model="Model",
        capabilities=PrinterCapabilities(250, 210, 220, 0.4, 1.75),
        status=status,
        created_at=CREATED,
        updated_at=CREATED,
    )


def test_dispatch_starts_an_idle_printer_on_the_job() -> None:
    idle = printer(PrinterStatus.IDLE)
    print_job_id = PrintJobId.new()

    idle.dispatch(print_job_id, LATER)

    assert idle.status is PrinterStatus.PRINTING
    assert idle.print_job_id == print_job_id
    assert idle.progress_percent == 0
    assert idle.updated_at == LATER


@pytest.mark.parametrize("status", [s for s in PrinterStatus if s is not PrinterStatus.IDLE])
def test_dispatch_refuses_a_printer_that_is_not_idle(status: PrinterStatus) -> None:
    busy = printer(status)
    with pytest.raises(RuleViolation):
        busy.dispatch(PrintJobId.new(), LATER)
    assert busy.print_job_id is None


@pytest.mark.parametrize("status", [PrinterStatus.FINISHED, PrinterStatus.ERROR])
def test_release_frees_a_finished_or_faulted_printer(status: PrinterStatus) -> None:
    stopped = printer(status)
    stopped.print_job_id = PrintJobId.new()

    stopped.release(LATER)

    assert stopped.status is PrinterStatus.IDLE
    assert stopped.print_job_id is None


@pytest.mark.parametrize(
    "status", [s for s in PrinterStatus if s not in (PrinterStatus.FINISHED, PrinterStatus.ERROR)]
)
def test_release_refuses_a_printer_that_has_not_stopped(status: PrinterStatus) -> None:
    with pytest.raises(RuleViolation):
        printer(status).release(LATER)


MK4S = PrinterCapabilities(250, 210, 220, 0.4, 1.75)
FIELDS = [
    "build_volume_x_mm",
    "build_volume_y_mm",
    "build_volume_z_mm",
    "nozzle_diameter_mm",
    "filament_diameter_mm",
]


def test_capabilities_accept_a_real_printer() -> None:
    assert MK4S.nozzle_diameter_mm == 0.4


@pytest.mark.parametrize("field", FIELDS)
def test_capabilities_refuse_a_zero(field: str) -> None:
    with pytest.raises(RuleViolation):
        PrinterCapabilities(**{**vars(MK4S), field: 0})


def test_capabilities_refuse_a_negative_value() -> None:
    with pytest.raises(RuleViolation):
        PrinterCapabilities(**{**vars(MK4S), "nozzle_diameter_mm": -0.4})


def printer_of(model: str, capabilities: PrinterCapabilities = MK4S) -> Printer:
    return Printer(
        id=PrinterId.new(),
        name="Printer",
        model=model,
        capabilities=capabilities,
        status=PrinterStatus.IDLE,
        created_at=CREATED,
        updated_at=CREATED,
    )


def test_printer_types_collapse_identical_printers() -> None:
    assert printer_types([printer_of("MK4S"), printer_of("MK4S")]) == [PrinterType("MK4S", MK4S)]


def test_printer_types_split_one_model_by_nozzle() -> None:
    wide = PrinterCapabilities(250, 210, 220, 0.6, 1.75)

    types = printer_types([printer_of("MK4S"), printer_of("MK4S", wide)])

    assert types == [PrinterType("MK4S", MK4S), PrinterType("MK4S", wide)]


def test_printer_types_are_sorted_by_model() -> None:
    types = printer_types([printer_of("XL"), printer_of("CORE One"), printer_of("MINI+")])

    assert [each.model for each in types] == ["CORE One", "MINI+", "XL"]


def test_an_empty_fleet_has_no_printer_types() -> None:
    assert printer_types([]) == []
