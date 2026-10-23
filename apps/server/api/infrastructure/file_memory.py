# Stub: keeps file records in process memory, so the other apps can integrate before the server
# has a database. Everything is lost on restart. Replacing it means writing a SqlFileRepository
# that passes tests/contract/test_file_repository.py and constructing that in api/main.py.
from collections.abc import Iterable
from dataclasses import replace

from core_domain.ddd import EntityNotFound
from core_domain.file import File
from core_domain.ids import FileId


class InMemoryFileRepository:
    def __init__(self, files: Iterable[File] = ()) -> None:
        self._files = {file.id: file for file in files}

    async def get(self, entity_id: FileId) -> File:
        if entity_id not in self._files:
            raise EntityNotFound(entity_id)
        return replace(self._files[entity_id])

    async def get_many(self, file_ids: Iterable[FileId]) -> list[File]:
        return [replace(self._files[i]) for i in dict.fromkeys(file_ids) if i in self._files]

    async def save(self, entity: File) -> None:
        self._files[entity.id] = replace(entity)

    async def delete(self, file_id: FileId) -> None:
        if self._files.pop(file_id, None) is None:
            raise EntityNotFound(file_id)

    async def is_storage_key_used(self, storage_key: str) -> bool:
        return any(f.storage_key() == storage_key for f in self._files.values())
