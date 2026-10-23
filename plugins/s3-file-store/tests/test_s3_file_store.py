"""S3FileStore against a fake S3 client, so its error translation is tested without a store."""

import asyncio
from collections.abc import AsyncGenerator, AsyncIterator, Callable, Coroutine
from contextlib import asynccontextmanager

import aioboto3
import pytest
from botocore.exceptions import ClientError, EndpointConnectionError
from plugin_api.file_store import FileStore, FileStoreError, StoredFileNotFoundError

from s3_file_store import S3FileStore
from s3_file_store.s3_file_store import PART_SIZE

type Operation = Callable[[S3FileStore], Coroutine[object, object, object]]


async def stream(*chunks: bytes) -> AsyncIterator[bytes]:
    for chunk in chunks:
        yield chunk


async def read_all(store: S3FileStore, key: str) -> bytes:
    return b"".join([chunk async for chunk in await store.read(key)])


OPERATIONS: dict[str, Operation] = {
    "read": lambda store: read_all(store, "key"),
    "write": lambda store: store.write("key", stream(b"bytes")),
    "exists": lambda store: store.exists("key"),
    "delete": lambda store: store.delete("key"),
    "health_check": lambda store: store.health_check(),
}


def client_error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, "operation")


class FakeBody:
    def __init__(self, data: bytes) -> None:
        self._data = data

    # Like aiobotocore's StreamingBody, entering yields the raw response, not the body.
    async def __aenter__(self) -> object:
        return object()

    async def __aexit__(self, *_: object) -> None:
        return None

    async def iter_chunks(self, chunk_size: int) -> AsyncIterator[bytes]:
        for start in range(0, len(self._data), chunk_size):
            yield self._data[start : start + chunk_size]


class FakeS3Client:
    """Holds objects in memory, or raises `error` from every call when it is set. A multipart
    upload becomes an object only when it completes."""

    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.uploads: dict[str, dict[int, bytes]] = {}
        self.aborted: list[str] = []
        self.error: Exception | None = None

    def _fail_if_set(self) -> None:
        if self.error is not None:
            raise self.error

    async def get_object(self, *, Bucket: str, Key: str) -> dict[str, FakeBody]:
        self._fail_if_set()
        if Key not in self.objects:
            raise client_error("NoSuchKey")
        return {"Body": FakeBody(self.objects[Key])}

    async def head_object(self, *, Bucket: str, Key: str) -> None:
        self._fail_if_set()
        if Key not in self.objects:
            raise client_error("404")

    async def put_object(self, *, Bucket: str, Key: str, Body: bytes) -> None:
        self._fail_if_set()
        self.objects[Key] = Body

    async def create_multipart_upload(self, *, Bucket: str, Key: str) -> dict[str, str]:
        self._fail_if_set()
        upload_id = f"upload-{len(self.uploads)}"
        self.uploads[upload_id] = {}
        return {"UploadId": upload_id}

    async def upload_part(
        self, *, Bucket: str, Key: str, UploadId: str, PartNumber: int, Body: bytes
    ) -> dict[str, str]:
        self._fail_if_set()
        self.uploads[UploadId][PartNumber] = Body
        return {"ETag": f"etag-{PartNumber}"}

    async def complete_multipart_upload(
        self,
        *,
        Bucket: str,
        Key: str,
        UploadId: str,
        MultipartUpload: dict[str, list[dict[str, object]]],
    ) -> None:
        self._fail_if_set()
        parts = self.uploads.pop(UploadId)
        numbers = [part["PartNumber"] for part in MultipartUpload["Parts"]]
        self.objects[Key] = b"".join(parts[number] for number in numbers if isinstance(number, int))

    async def abort_multipart_upload(self, *, Bucket: str, Key: str, UploadId: str) -> None:
        self.aborted.append(UploadId)
        self.uploads.pop(UploadId, None)

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
        endpoint_url="http://localhost",
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


def test_a_small_file_is_put_whole_and_reads_back(client: FakeS3Client) -> None:
    async def write_then_read(store: S3FileStore) -> bytes:
        await store.write("key", stream(b"by", b"tes"))
        return await read_all(store, "key")

    assert run(new_store(), write_then_read) == b"bytes"
    assert not client.uploads


def test_a_large_file_is_uploaded_in_parts_and_reads_back(client: FakeS3Client) -> None:
    data = bytes(range(256)) * (PART_SIZE // 256 * 2 + 3)

    async def write_then_read(store: S3FileStore) -> bytes:
        await store.write("key", stream(data[:1000], data[1000:]))
        return await read_all(store, "key")

    assert run(new_store(), write_then_read) == data
    assert not client.uploads


def test_a_source_that_fails_part_way_stores_nothing(client: FakeS3Client) -> None:
    client.objects["key"] = b"original"

    async def failing() -> AsyncIterator[bytes]:
        yield b"x" * PART_SIZE
        raise ValueError("rejected")

    with pytest.raises(ValueError, match="rejected"):
        run(new_store(), lambda store: store.write("key", failing()))
    assert client.objects["key"] == b"original"
    assert client.aborted == ["upload-0"]


def test_exists_reports_whether_a_file_is_stored(client: FakeS3Client) -> None:
    client.objects["key"] = b"bytes"
    assert run(new_store(), lambda store: store.exists("key")) is True
    assert run(new_store(), lambda store: store.exists("other")) is False


def test_a_missing_file_raises_stored_file_not_found(client: FakeS3Client) -> None:
    with pytest.raises(StoredFileNotFoundError):
        run(new_store(), lambda store: store.read("key"))


@pytest.mark.parametrize("name", OPERATIONS)
def test_a_refused_request_raises_file_store_error(client: FakeS3Client, name: str) -> None:
    client.error = client_error("AccessDenied")
    with pytest.raises(FileStoreError) as raised:
        run(new_store(), OPERATIONS[name])
    assert type(raised.value) is FileStoreError


@pytest.mark.parametrize("name", OPERATIONS)
def test_an_unreachable_store_raises_file_store_error(client: FakeS3Client, name: str) -> None:
    client.error = EndpointConnectionError(endpoint_url="http://localhost")
    with pytest.raises(FileStoreError):
        run(new_store(), OPERATIONS[name])


@pytest.mark.parametrize("name", OPERATIONS)
def test_use_before_opening_raises_file_store_error(client: FakeS3Client, name: str) -> None:
    with pytest.raises(FileStoreError):
        asyncio.run(OPERATIONS[name](new_store()))
