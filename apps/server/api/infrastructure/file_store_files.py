# Stub: the file domain's bytes in the deployment's FileStore plugin. For now it only owns the
# store's lifetime and health; MockFileStorage still serves the domain's FileStorage port, because
# the server has no endpoints for file bytes yet. Filling it in means reading, writing and deleting
# a file's bytes here by a storage key built from its FileId, turning StoredFileNotFoundError into
# EntityNotFound(file_id), and passing it to FileService in api/main.py in place of
# MockFileStorage.
from collections.abc import Callable, Generator
from contextlib import AsyncExitStack, contextmanager
from types import TracebackType
from typing import Self

from core_domain.ddd import Unavailable
from plugin_api.file_store import FileStore, FileStoreError

_DEPENDENCY = "file storage"


@contextmanager
def _store_errors() -> Generator[None]:
    try:
        yield
    except FileStoreError as error:
        raise Unavailable(_DEPENDENCY) from error


class FileStoreFiles:
    """Builds the store when opened, not when constructed, so importing the app reads no
    configuration."""

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

    def _opened(self) -> FileStore:
        if self._store is None:
            raise Unavailable(_DEPENDENCY)
        return self._store

    async def health_check(self) -> None:
        """Raises Unavailable if the store cannot be reached or is not open."""
        with _store_errors():
            await self._opened().health_check()
