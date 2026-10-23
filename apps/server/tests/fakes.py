"""An in-memory FileStore for tests, keeping the port's promise that a failed write stores
nothing."""

from collections.abc import AsyncIterable, AsyncIterator
from types import TracebackType
from typing import Self

from plugin_api.file_store import FileStoreError, StoredFileNotFoundError


class MemoryFileStore:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.healthy = True

    def _fail_if_unhealthy(self) -> None:
        if not self.healthy:
            raise FileStoreError("localhost:3900 refused the connection")

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    async def read(self, key: str) -> AsyncIterator[bytes]:
        self._fail_if_unhealthy()
        if key not in self.objects:
            raise StoredFileNotFoundError(key)
        data = self.objects[key]

        async def chunks() -> AsyncIterator[bytes]:
            for start in range(0, len(data), 4):
                yield data[start : start + 4]

        return chunks()

    async def write(self, key: str, chunks: AsyncIterable[bytes]) -> None:
        self._fail_if_unhealthy()
        self.objects[key] = b"".join([chunk async for chunk in chunks])

    async def exists(self, key: str) -> bool:
        self._fail_if_unhealthy()
        return key in self.objects

    async def delete(self, key: str) -> None:
        self._fail_if_unhealthy()
        self.objects.pop(key, None)

    async def health_check(self) -> None:
        self._fail_if_unhealthy()
