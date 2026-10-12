"""S3FileStore against a fake S3 client, so its error translation is tested without a store."""

import asyncio
from collections.abc import AsyncGenerator, Callable, Coroutine
from contextlib import asynccontextmanager

import aioboto3
import pytest
from botocore.exceptions import ClientError, EndpointConnectionError
from plugin_api.file_store import FileStore, FileStoreError, StoredFileNotFoundError

from s3_file_store import S3FileStore

type Operation = Callable[[S3FileStore], Coroutine[object, object, object]]

OPERATIONS: dict[str, Operation] = {
    "read": lambda store: store.read("key"),
    "write": lambda store: store.write("key", b"bytes"),
    "delete": lambda store: store.delete("key"),
    "health_check": lambda store: store.health_check(),
}


def client_error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, "operation")


class FakeBody:
    def __init__(self, data: bytes) -> None:
        self._data = data

    async def __aenter__(self) -> "FakeBody":
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    async def read(self) -> bytes:
        return self._data


class FakeS3Client:
    """Holds objects in memory, or raises `error` from every call when it is set."""

    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.error: Exception | None = None

    def _fail_if_set(self) -> None:
        if self.error is not None:
            raise self.error

    async def get_object(self, *, Bucket: str, Key: str) -> dict[str, FakeBody]:
        self._fail_if_set()
        if Key not in self.objects:
            raise client_error("NoSuchKey")
        return {"Body": FakeBody(self.objects[Key])}

    async def put_object(self, *, Bucket: str, Key: str, Body: bytes) -> None:
        self._fail_if_set()
        self.objects[Key] = Body

    async def delete_object(self, *, Bucket: str, Key: str) -> None:
        self._fail_if_set()
        self.objects.pop(Key, None)

    async def head_bucket(self, *, Bucket: str) -> None:
        self._fail_if_set()


class FakeSession:
    def __init__(self, client: FakeS3Client) -> None:
        self._client = client

    @asynccontextmanager
    async def client(self, *_: object, **__: object) -> AsyncGenerator[FakeS3Client]:
        yield self._client


def new_store() -> S3FileStore:
    return S3FileStore(
        endpoint_url="http://store.invalid",
        region_name="region",
        bucket="bucket",
        access_key="access",
        secret_key="secret",
    )


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> FakeS3Client:
    fake = FakeS3Client()

    def session(**_: object) -> FakeSession:
        return FakeSession(fake)

    monkeypatch.setattr(aioboto3, "Session", session)
    return fake


def run(store: S3FileStore, operation: Operation) -> object:
    async def opened() -> object:
        async with store:
            return await operation(store)

    return asyncio.run(opened())


def accepts_a_file_store(store: FileStore) -> None:
    """Pyright checks the call below, so a drift between adapter and port fails type checking."""


def test_s3_file_store_satisfies_the_port() -> None:
    accepts_a_file_store(new_store())


def test_a_written_file_reads_back(client: FakeS3Client) -> None:
    async def write_then_read(store: S3FileStore) -> bytes:
        await store.write("key", b"bytes")
        return await store.read("key")

    assert run(new_store(), write_then_read) == b"bytes"


def test_a_missing_file_raises_stored_file_not_found(client: FakeS3Client) -> None:
    with pytest.raises(StoredFileNotFoundError):
        run(new_store(), OPERATIONS["read"])


@pytest.mark.parametrize("name", OPERATIONS)
def test_a_refused_request_raises_file_store_error(client: FakeS3Client, name: str) -> None:
    client.error = client_error("AccessDenied")
    with pytest.raises(FileStoreError) as raised:
        run(new_store(), OPERATIONS[name])
    assert type(raised.value) is FileStoreError


@pytest.mark.parametrize("name", OPERATIONS)
def test_an_unreachable_store_raises_file_store_error(client: FakeS3Client, name: str) -> None:
    client.error = EndpointConnectionError(endpoint_url="http://store.invalid")
    with pytest.raises(FileStoreError):
        run(new_store(), OPERATIONS[name])


@pytest.mark.parametrize("name", OPERATIONS)
def test_use_before_opening_raises_file_store_error(client: FakeS3Client, name: str) -> None:
    with pytest.raises(FileStoreError):
        asyncio.run(OPERATIONS[name](new_store()))
