import re
from datetime import UTC, datetime
from pathlib import Path

import pytest

from core_domain.ddd import RuleViolation
from core_domain.ids import PrinterId, PrintJobId
from core_domain.printer import Printer, PrinterStatus

PROTO = Path(__file__).resolve().parents[2] / "proto" / "printer" / "v1" / "printer.proto"
CREATED = datetime(2026, 10, 1, tzinfo=UTC)
LATER = datetime(2026, 10, 2, tzinfo=UTC)


def test_status_mirrors_the_proto_enum() -> None:
    """Read as text, because core-domain may not depend on protobuf."""
    proto_values = re.findall(r"^\s*PRINTER_STATUS_(\w+)\s*=", PROTO.read_text(), re.MULTILINE)
    assert [v for v in proto_values if v != "UNSPECIFIED"] == [s.name for s in PrinterStatus]


def printer(status: PrinterStatus) -> Printer:
    return Printer(PrinterId.new(), "Printer", "Model", status, CREATED, CREATED)


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
