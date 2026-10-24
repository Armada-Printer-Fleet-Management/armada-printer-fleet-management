from abc import abstractmethod
from collections.abc import Iterable

from core_domain.ddd import AbstractReadRepository
from core_domain.file import File
from core_domain.ids import FileId


class FileRepository(AbstractReadRepository[FileId, File]):
    """File records as the application server keeps them. Read only. Implementations live in
    armada_infrastructure."""

    @abstractmethod
    def files(self, file_ids: Iterable[FileId]) -> list[File]:
        """An unknown ID is left out."""
