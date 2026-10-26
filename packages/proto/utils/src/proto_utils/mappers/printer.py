from datetime import UTC

from core_domain import ids
from core_domain.printer import Printer, PrinterStatus

from proto_utils.gen.common.v1.time_status_pb2 import TimeStatus
from proto_utils.gen.id.v1.print_job_id_pb2 import PrintJobId
from proto_utils.gen.id.v1.printer_id_pb2 import PrinterId
from proto_utils.gen.printer.v1 import printer_pb2
from proto_utils.mapper import ProtoMapper

_STATUS_PREFIX = "PRINTER_STATUS_"


class PrinterMapper(ProtoMapper[Printer, printer_pb2.Printer]):
    def to_proto(self, entity: Printer) -> printer_pb2.Printer:
        return printer_pb2.Printer(
            id=self.id_to_proto(PrinterId, entity.id),
            name=entity.name,
            model=entity.model,
            status=_STATUS_PREFIX + entity.status.name,
            print_job_id=self.optional_id_to_proto(PrintJobId, entity.print_job_id),
            progress_percent=entity.progress_percent,
            time_status=TimeStatus(created_at=entity.created_at, updated_at=entity.updated_at),
        )

    def to_entity(self, message: printer_pb2.Printer) -> Printer:
        status_name = printer_pb2.PrinterStatus.Name(message.status)
        if status_name not in {_STATUS_PREFIX + s.name for s in PrinterStatus}:
            raise ValueError(f"{status_name} is not a valid printer status")
        return Printer(
            id=self.id_from_proto(ids.PrinterId, message.id),
            name=message.name,
            model=message.model,
            status=PrinterStatus[status_name.removeprefix(_STATUS_PREFIX)],
            created_at=message.time_status.created_at.ToDatetime(UTC),
            updated_at=message.time_status.updated_at.ToDatetime(UTC),
            print_job_id=self.optional_id_from_proto(ids.PrintJobId, message.print_job_id),
            progress_percent=(
                message.progress_percent if message.HasField("progress_percent") else None
            ),
        )
