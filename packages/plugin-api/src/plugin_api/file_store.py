from collections.abc import AsyncIterable, AsyncIterator
from types import TracebackType
from typing import Protocol, Self


class FileStore(Protocol):
    """
    A protocol for a file store.

    Any error with the file store itself will raise a FileStoreError. If a file is not found, a
    StoredFileNotFoundError will be raised.
    A key is a non-empty string chosen by the caller. The store treats it as an opaque name.

    A store is opened with `async with` before use and closed when that block exits, so whoever
    owns it can manage its lifetime without knowing which store it is.
    """

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...

    async def read(self, key: str) -> AsyncIterator[bytes]:
        """
        Get a file from the store as a stream of chunks.

        raises StoredFileNotFoundError when awaited if the file is not found, before any chunk is
        read, so a caller can still report it before it starts sending the file on.
        """
        ...

    async def write(self, key: str, chunks: AsyncIterable[bytes]) -> None:
        """
        Put a file into the store from a stream of chunks.

        If an existing file with the same key exists, it will be overwritten. If `chunks` raises,
        nothing is stored, any existing file is left unchanged, and that exception propagates as
        it is rather than as a FileStoreError, so a caller can reject a file part way through.
        """
        ...

    async def exists(self, key: str) -> bool:
        """Whether a file is stored under the key."""
        ...

    async def delete(self, key: str) -> None:
        """
        Delete a file from the store.

        Nothing is done if the file does not exist.
        """
        ...

    async def health_check(self) -> None:
        """
        Check the health of the store.

        raises FileStoreError if the store cannot be reached or is not usable.
        """
        ...


class FileStoreError(Exception):
    """Raised when there is an error with the file store."""


class StoredFileNotFoundError(FileStoreError):
    """Raised when a file is not found in the store."""
