from collections.abc import AsyncIterable, AsyncIterator, Generator
from contextlib import AsyncExitStack, contextmanager, suppress
from types import TracebackType
from typing import TYPE_CHECKING, Self

import aioboto3
from aiobotocore.config import AioConfig
from botocore.exceptions import BotoCoreError, ClientError
from plugin_api.file_store import FileStoreError, StoredFileNotFoundError

# The stubs are a dev dependency, so they must not be imported at runtime.
if TYPE_CHECKING:
    from types_aiobotocore_s3 import S3Client
    from types_aiobotocore_s3.type_defs import CompletedPartTypeDef

DEFAULT_CLIENT_CONFIG = AioConfig(
    connect_timeout=2,
    read_timeout=30,
    retries={"total_max_attempts": 2, "mode": "standard"},
)

# S3 refuses multipart parts under 5 MiB, except the last. A write buffers at most one part.
PART_SIZE = 8 * 1024 * 1024
READ_CHUNK_SIZE = 64 * 1024

# HEAD responses have no body, so a missing object reports only its status code.
_MISSING_OBJECT_CODES = {"NoSuchKey", "NotFound", "404"}


def _is_missing_object(error: ClientError) -> bool:
    return error.response.get("Error", {}).get("Code") in _MISSING_OBJECT_CODES


@contextmanager
def _s3_errors(action: str) -> Generator[None]:
    try:
        yield
    except (ClientError, BotoCoreError) as e:
        raise FileStoreError(f"S3 {action} failed") from e


class S3FileStore:
    def __init__(
        self,
        *,
        endpoint_url: str,
        region_name: str,
        bucket: str,
        access_key: str,
        secret_key: str,
        config: AioConfig | None = None,
    ) -> None:
        self._endpoint_url = endpoint_url
        # A caller's config overrides the defaults. Path-style is merged last so it cannot be
        # dropped: stores such as Garage do not serve buckets as subdomains unless configured to.
        path_style = AioConfig(s3={"addressing_style": "path"})
        merged = DEFAULT_CLIENT_CONFIG.merge(config) if config else DEFAULT_CLIENT_CONFIG
        self._config = merged.merge(path_style)
        self._bucket = bucket
        self._session = aioboto3.Session(
            aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=region_name
        )
        self._exit_stack = AsyncExitStack()
        self._client: S3Client | None = None

    async def __aenter__(self) -> Self:
        self._client = await self._exit_stack.enter_async_context(
            # Only the S3 stubs are installed, so client()'s other service overloads are Unknown.
            self._session.client(  # pyright: ignore[reportUnknownMemberType]
                "s3",
                endpoint_url=self._endpoint_url,
                config=self._config,
            )
        )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self._client = None
        await self._exit_stack.aclose()

    def _s3_client(self) -> "S3Client":
        if self._client is None:
            raise FileStoreError("S3FileStore must be opened with 'async with' before use")
        return self._client

    async def read(self, key: str) -> AsyncIterator[bytes]:
        """
        Get a file from the store as a stream of chunks.

        raises StoredFileNotFoundError if the file is not found.
        """
        try:
            response = await self._s3_client().get_object(Bucket=self._bucket, Key=key)
        except ClientError as e:
            if _is_missing_object(e):
                raise StoredFileNotFoundError(key) from e
            raise FileStoreError("S3 read failed") from e
        except BotoCoreError as e:
            raise FileStoreError("S3 read failed") from e

        body = response["Body"]

        async def chunks() -> AsyncIterator[bytes]:
            with _s3_errors("read"):
                # Entering the body yields the raw HTTP response, which has no iter_chunks.
                async with body:
                    async for chunk in body.iter_chunks(READ_CHUNK_SIZE):
                        yield chunk

        return chunks()

    async def write(self, key: str, chunks: AsyncIterable[bytes]) -> None:
        """
        Put a file into the store from a stream of chunks.

        A file larger than one part goes up as a multipart upload, which S3 does not make visible
        until it completes, so aborting it on any error stores nothing.
        """
        client = self._s3_client()
        buffer = bytearray()
        upload_id: str | None = None
        parts: list[CompletedPartTypeDef] = []
        completed = False

        async def upload_part(body: bytes) -> None:
            nonlocal upload_id
            with _s3_errors("write"):
                if upload_id is None:
                    created = await client.create_multipart_upload(Bucket=self._bucket, Key=key)
                    upload_id = created["UploadId"]
                part_number = len(parts) + 1
                uploaded = await client.upload_part(
                    Bucket=self._bucket,
                    Key=key,
                    UploadId=upload_id,
                    PartNumber=part_number,
                    Body=body,
                )
            parts.append({"ETag": uploaded["ETag"], "PartNumber": part_number})

        try:
            async for chunk in chunks:
                buffer += chunk
                while len(buffer) >= PART_SIZE:
                    await upload_part(bytes(buffer[:PART_SIZE]))
                    del buffer[:PART_SIZE]

            if upload_id is None:
                with _s3_errors("write"):
                    await client.put_object(Bucket=self._bucket, Key=key, Body=bytes(buffer))
                return
            if buffer:
                await upload_part(bytes(buffer))
            with _s3_errors("write"):
                await client.complete_multipart_upload(
                    Bucket=self._bucket,
                    Key=key,
                    UploadId=upload_id,
                    MultipartUpload={"Parts": parts},
                )
            completed = True
        finally:
            if upload_id is not None and not completed:
                # The original error is the one to report. Parts left by a failed abort are not
                # visible as an object.
                with suppress(ClientError, BotoCoreError):
                    await client.abort_multipart_upload(
                        Bucket=self._bucket, Key=key, UploadId=upload_id
                    )

    async def exists(self, key: str) -> bool:
        """Whether a file is stored under the key."""
        try:
            await self._s3_client().head_object(Bucket=self._bucket, Key=key)
        except ClientError as e:
            if _is_missing_object(e):
                return False
            raise FileStoreError("S3 exists check failed") from e
        except BotoCoreError as e:
            raise FileStoreError("S3 exists check failed") from e
        return True

    async def delete(self, key: str) -> None:
        """
        Delete a file from the store.

        Nothing is done if the file does not exist.
        """
        with _s3_errors("delete"):
            await self._s3_client().delete_object(Bucket=self._bucket, Key=key)

    async def health_check(self) -> None:
        """
        Check the health of the store.

        raises FileStoreError if the store cannot be reached or the bucket is unavailable.
        """
        with _s3_errors("health check"):
            await self._s3_client().head_bucket(Bucket=self._bucket)
