from datetime import UTC

from core_domain import ids
from core_domain.print_job import PrintJob, PrintJobStatus

from proto_utils.gen.common.v1.time_status_pb2 import TimeStatus
from proto_utils.gen.id.v1.file_id_pb2 import FileId
from proto_utils.gen.id.v1.print_job_id_pb2 import PrintJobId
from proto_utils.gen.id.v1.printer_id_pb2 import PrinterId
from proto_utils.gen.id.v1.queue_id_pb2 import QueueId
from proto_utils.gen.id.v1.user_id_pb2 import UserId
from proto_utils.gen.print_job.v1 import print_job_pb2
from proto_utils.mapper import ProtoMapper

_STATUS_PREFIX = "PRINT_JOB_STATUS_"


class PrintJobMapper(ProtoMapper[PrintJob, print_job_pb2.PrintJob]):
    def to_proto(self, entity: PrintJob) -> print_job_pb2.PrintJob:
        return print_job_pb2.PrintJob(
            id=self.id_to_proto(PrintJobId, entity.id),
            user_id=self.id_to_proto(UserId, entity.user_id),
            queue_id=self.optional_id_to_proto(QueueId, entity.queue_id),
            file_id=self.optional_id_to_proto(FileId, entity.file_id),
            status=_STATUS_PREFIX + entity.status.name,
            user_notes=entity.user_notes,
            status_reason=entity.status_reason,
            printer_id=self.optional_id_to_proto(PrinterId, entity.printer_id),
            time_status=TimeStatus(created_at=entity.created_at, updated_at=entity.updated_at),
        )

    def to_entity(self, message: print_job_pb2.PrintJob) -> PrintJob:
        status_name = print_job_pb2.PrintJobStatus.Name(message.status)
        if status_name not in {_STATUS_PREFIX + s.name for s in PrintJobStatus}:
            raise ValueError(f"{status_name} is not a valid print job status")
        return PrintJob(
            id=self.id_from_proto(ids.PrintJobId, message.id),
            user_id=self.id_from_proto(ids.UserId, message.user_id),
            status=PrintJobStatus[status_name.removeprefix(_STATUS_PREFIX)],
            created_at=message.time_status.created_at.ToDatetime(UTC),
            updated_at=message.time_status.updated_at.ToDatetime(UTC),
            user_notes=message.user_notes,
            queue_id=self.optional_id_from_proto(ids.QueueId, message.queue_id),
            file_id=self.optional_id_from_proto(ids.FileId, message.file_id),
            status_reason=message.status_reason if message.HasField("status_reason") else None,
            printer_id=self.optional_id_from_proto(ids.PrinterId, message.printer_id),
        )
