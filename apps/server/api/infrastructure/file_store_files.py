from collections.abc import AsyncIterable, AsyncIterator, Callable, Generator
from contextlib import AsyncExitStack, contextmanager
from types import TracebackType
from typing import Self

from core_domain.ddd import EntityNotFound, Unavailable
from core_domain.file import File
from plugin_api.file_store import FileStore, FileStoreError, StoredFileNotFoundError

_DEPENDENCY = "file storage"


@contextmanager
def _store_errors() -> Generator[None]:
    try:
        yield
    except FileStoreError as error:
        raise Unavailable(_DEPENDENCY) from error


class FileStoreFiles:
    """The file domain's bytes in the deployment's FileStore plugin. Builds the store when
    opened, not when constructed, so importing the app reads no configuration."""

    def __init__(self, open_store: Callable[[], FileStore]) -> None:
        self._open_store = open_store
        self._exit_stack = AsyncExitStack()
        self._store: FileStore | None = None

    async def __aenter__(self) -> Self:
        with _store_errors():
            self._store = await self._exit_stack.enter_async_context(self._open_store())
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self._store = None
        await self._exit_stack.aclose()

    def _file_store(self) -> FileStore:
        if self._store is None:
            raise Unavailable(_DEPENDENCY)
        return self._store

    async def health_check(self) -> None:
        """Raises Unavailable if the store cannot be reached or is not open."""
        with _store_errors():
            await self._file_store().health_check()

    async def has_upload(self, file: File) -> bool:
        with _store_errors():
            return await self._file_store().exists(file.storage_key())

    async def write(self, file: File, chunks: AsyncIterable[bytes]) -> None:
        with _store_errors():
            await self._file_store().write(file.storage_key(), chunks)

    async def read(self, file: File) -> AsyncIterator[bytes]:
        try:
            stored = await self._file_store().read(file.storage_key())
        except StoredFileNotFoundError as error:
            raise EntityNotFound(file.id) from error
        except FileStoreError as error:
            raise Unavailable(_DEPENDENCY) from error

        async def chunks() -> AsyncIterator[bytes]:
            with _store_errors():
                async for chunk in stored:
                    yield chunk

        return chunks()

    async def delete(self, file: File) -> None:
        with _store_errors():
            await self._file_store().delete(file.storage_key())
