from collections.abc import AsyncIterable, AsyncIterator
from typing import Protocol

from core_domain.file import File


class FileStorage(Protocol):
    """Where file bytes live, apart from the database. Implementations are in api/infrastructure."""

    async def has_upload(self, file: File) -> bool:
        """Whether the file's bytes have been stored."""
        ...

    async def write(self, file: File, chunks: AsyncIterable[bytes]) -> None:
        """Stores the file's bytes. If chunks raises, nothing is stored and the error propagates."""
        ...

    async def read(self, file: File) -> AsyncIterator[bytes]:
        """The file's bytes. Raises EntityNotFound for the file's ID if none are stored."""
        ...

    async def delete(self, file: File) -> None:
        """Removes the file's bytes, if any are stored."""
        ...
