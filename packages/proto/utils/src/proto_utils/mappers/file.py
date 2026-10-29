from datetime import UTC

from core_domain import ids
from core_domain.file import File, FileType

from proto_utils.gen.common.v1.time_status_pb2 import TimeStatus
from proto_utils.gen.file.v1 import file_pb2
from proto_utils.gen.id.v1.file_id_pb2 import FileId
from proto_utils.gen.id.v1.user_id_pb2 import UserId
from proto_utils.mapper import ProtoMapper

_TYPE_PREFIX = "FILE_TYPE_"


class FileMapper(ProtoMapper[File, file_pb2.File]):
    def to_proto(self, entity: File) -> file_pb2.File:
        return file_pb2.File(
            id=self.id_to_proto(FileId, entity.id),
            user_id=self.id_to_proto(UserId, entity.user_id),
            filename=entity.filename,
            file_type=_TYPE_PREFIX + entity.file_type.name,
            size_bytes=entity.size_bytes,
            sha256=entity.sha256,
            time_status=TimeStatus(created_at=entity.created_at, updated_at=entity.updated_at),
        )

    def to_entity(self, message: file_pb2.File) -> File:
        return File(
            id=self.id_from_proto(ids.FileId, message.id),
            user_id=self.id_from_proto(ids.UserId, message.user_id),
            filename=message.filename,
            file_type=self.file_type_from_proto(message.file_type),
            size_bytes=message.size_bytes,
            sha256=message.sha256,
            created_at=message.time_status.created_at.ToDatetime(UTC),
            updated_at=message.time_status.updated_at.ToDatetime(UTC),
        )

    @staticmethod
    def file_type_from_proto(file_type: file_pb2.FileType) -> FileType:
        """Raises ValueError for FILE_TYPE_UNSPECIFIED or a value this build does not know."""
        name = file_pb2.FileType.Name(file_type).removeprefix(_TYPE_PREFIX)
        if name not in FileType.__members__:
            raise ValueError(f"{_TYPE_PREFIX}{name} is not a valid file type")
        return FileType[name]
