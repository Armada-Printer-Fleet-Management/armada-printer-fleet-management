from datetime import UTC

from core_domain import ids
from core_domain.printer_queue import PrinterQueue

from proto_utils.gen.common.v1.time_status_pb2 import TimeStatus
from proto_utils.gen.id.v1.printer_queue_id_pb2 import PrinterQueueId
from proto_utils.gen.printer_queue.v1 import printer_queue_pb2
from proto_utils.mapper import ProtoMapper


class PrinterQueueMapper(ProtoMapper[PrinterQueue, printer_queue_pb2.PrinterQueue]):
    def to_proto(self, entity: PrinterQueue) -> printer_queue_pb2.PrinterQueue:
        return printer_queue_pb2.PrinterQueue(
            id=self.id_to_proto(PrinterQueueId, entity.id),
            name=entity.name,
            is_active=entity.is_active,
            time_status=TimeStatus(created_at=entity.created_at, updated_at=entity.updated_at),
        )

    def to_entity(self, message: printer_queue_pb2.PrinterQueue) -> PrinterQueue:
        return PrinterQueue(
            id=self.id_from_proto(ids.PrinterQueueId, message.id),
            name=message.name,
            is_active=message.is_active,
            created_at=message.time_status.created_at.ToDatetime(UTC),
            updated_at=message.time_status.updated_at.ToDatetime(UTC),
        )
