from datetime import UTC

from core_domain import ids
from core_domain.fleet import Printer, PrinterCapabilities, PrinterStatus, PrinterType

from proto_utils.gen.common.v1.time_status_pb2 import TimeStatus
from proto_utils.gen.fleet.v1 import printer_capabilities_pb2, printer_pb2, printer_type_pb2
from proto_utils.gen.id.v1.print_job_id_pb2 import PrintJobId
from proto_utils.gen.id.v1.printer_id_pb2 import PrinterId
from proto_utils.mapper import ProtoMapper

_STATUS_PREFIX = "PRINTER_STATUS_"


class PrinterMapper(ProtoMapper[Printer, printer_pb2.Printer]):
    def to_proto(self, entity: Printer) -> printer_pb2.Printer:
        return printer_pb2.Printer(
            id=self.id_to_proto(PrinterId, entity.id),
            name=entity.name,
            model=entity.model,
            capabilities=_capabilities_to_proto(entity.capabilities),
            status=_STATUS_PREFIX + entity.status.name,
            print_job_id=self.optional_id_to_proto(PrintJobId, entity.print_job_id),
            progress_percent=entity.progress_percent,
            time_status=TimeStatus(created_at=entity.created_at, updated_at=entity.updated_at),
        )

    def to_entity(self, message: printer_pb2.Printer) -> Printer:
        status_name = printer_pb2.PrinterStatus.Name(message.status)
        if status_name not in {_STATUS_PREFIX + s.name for s in PrinterStatus}:
            raise ValueError(f"{status_name} is not a valid printer status")
        if not message.HasField("capabilities"):
            raise ValueError("A printer must carry its capabilities")
        return Printer(
            id=self.id_from_proto(ids.PrinterId, message.id),
            name=message.name,
            model=message.model,
            capabilities=_capabilities_to_entity(message.capabilities),
            status=PrinterStatus[status_name.removeprefix(_STATUS_PREFIX)],
            created_at=message.time_status.created_at.ToDatetime(UTC),
            updated_at=message.time_status.updated_at.ToDatetime(UTC),
            print_job_id=self.optional_id_from_proto(ids.PrintJobId, message.print_job_id),
            progress_percent=(
                message.progress_percent if message.HasField("progress_percent") else None
            ),
        )


class PrinterTypeMapper(ProtoMapper[PrinterType, printer_type_pb2.PrinterType]):
    def to_proto(self, entity: PrinterType) -> printer_type_pb2.PrinterType:
        return printer_type_pb2.PrinterType(
            model=entity.model, capabilities=_capabilities_to_proto(entity.capabilities)
        )

    def to_entity(self, message: printer_type_pb2.PrinterType) -> PrinterType:
        if not message.HasField("capabilities"):
            raise ValueError("A printer type must carry its capabilities")
        return PrinterType(message.model, _capabilities_to_entity(message.capabilities))


def _capabilities_to_proto(
    capabilities: PrinterCapabilities,
) -> printer_capabilities_pb2.PrinterCapabilities:
    return printer_capabilities_pb2.PrinterCapabilities(
        build_volume_x_mm=capabilities.build_volume_x_mm,
        build_volume_y_mm=capabilities.build_volume_y_mm,
        build_volume_z_mm=capabilities.build_volume_z_mm,
        nozzle_diameter_mm=capabilities.nozzle_diameter_mm,
        filament_diameter_mm=capabilities.filament_diameter_mm,
    )


def _capabilities_to_entity(
    message: printer_capabilities_pb2.PrinterCapabilities,
) -> PrinterCapabilities:
    """Raises RuleViolation for a capability that is not greater than zero."""
    return PrinterCapabilities(
        build_volume_x_mm=message.build_volume_x_mm,
        build_volume_y_mm=message.build_volume_y_mm,
        build_volume_z_mm=message.build_volume_z_mm,
        nozzle_diameter_mm=message.nozzle_diameter_mm,
        filament_diameter_mm=message.filament_diameter_mm,
    )
