"""Fakes of the plugin ports for tests: an in-memory FileStore, keeping the port's promise that a
failed write stores nothing, a TokenVerifier that answers as it is told, and an in-memory
IdentityDirectory."""

from collections.abc import AsyncIterable, AsyncIterator
from types import TracebackType
from typing import Self
from uuid import uuid4

from plugin_api.file_store import FileStoreError, StoredFileNotFoundError
from plugin_api.identity_directory import (
    AccountExistsError,
    IdentityDirectoryError,
    NewAccount,
)
from plugin_api.token_verifier import VerifiedToken


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


class FakeTokenVerifier:
    """Verifies every token as `verified`, or raises `error` from every call when it is set."""

    def __init__(self, verified: VerifiedToken, error: Exception | None = None) -> None:
        self.verified = verified
        self.error = error

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    async def verify(self, token: str) -> VerifiedToken:
        if self.error is not None:
            raise self.error
        return self.verified

    async def health_check(self) -> None:
        if self.error is not None:
            raise self.error


class MemoryIdentityDirectory:
    """Accounts held in memory, keeping the port's promises: a duplicate email is refused, and a
    failed call leaves nothing behind. Set `healthy` to False to make every call fail."""

    def __init__(self) -> None:
        self.accounts: dict[str, NewAccount] = {}
        self.healthy = True

    def _fail_if_unhealthy(self) -> None:
        if not self.healthy:
            raise IdentityDirectoryError("localhost:8080 refused the connection")

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    async def create_account(self, account: NewAccount) -> str:
        self._fail_if_unhealthy()
        if any(existing.email == account.email for existing in self.accounts.values()):
            raise AccountExistsError("An account with this email already exists")
        subject = str(uuid4())
        self.accounts[subject] = account
        return subject

    async def delete_account(self, subject: str) -> None:
        self._fail_if_unhealthy()
        self.accounts.pop(subject, None)

    async def health_check(self) -> None:
        self._fail_if_unhealthy()
