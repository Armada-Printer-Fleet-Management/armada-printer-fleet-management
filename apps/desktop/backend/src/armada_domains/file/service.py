from collections.abc import Iterable

from core_domain.ddd import Service
from core_domain.file import File
from core_domain.ids import FileId

from armada_domains.file.repository import FileRepository


class FileService(Service[FileRepository]):
    def get(self, file_id: FileId) -> File:
        return self._repository.get(file_id)

    def files(self, file_ids: Iterable[FileId]) -> list[File]:
        return self._repository.files(file_ids)
