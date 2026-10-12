from contextlib import AsyncExitStack
from types import TracebackType
from typing import TYPE_CHECKING, Self

import aioboto3
from aiobotocore.config import AioConfig
from botocore.exceptions import BotoCoreError, ClientError
from plugin_api.file_store import FileStoreError, StoredFileNotFoundError

# The stubs are a dev dependency, so they must not be imported at runtime.
if TYPE_CHECKING:
    from types_aiobotocore_s3 import S3Client

DEFAULT_CLIENT_CONFIG = AioConfig(
    connect_timeout=2,
    read_timeout=30,
    retries={"total_max_attempts": 2, "mode": "standard"},
)


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

    async def read(self, key: str) -> bytes:
        """
        Get a file from the store.

        raises StoredFileNotFoundError if the file is not found.
        """
        try:
            response = await self._s3_client().get_object(Bucket=self._bucket, Key=key)
            async with response["Body"] as stream:
                return await stream.read()
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "NoSuchKey":
                raise StoredFileNotFoundError(key) from e
            raise FileStoreError("S3 read failed") from e
        except BotoCoreError as e:
            raise FileStoreError("S3 read failed") from e

    async def write(self, key: str, file: bytes) -> None:
        """
        Put a file into the store.

        If an existing file with the same key exists, it will be overwritten.
        """
        try:
            await self._s3_client().put_object(Bucket=self._bucket, Key=key, Body=file)
        except ClientError as e:
            raise FileStoreError("S3 write failed") from e
        except BotoCoreError as e:
            raise FileStoreError("S3 write failed") from e

    async def delete(self, key: str) -> None:
        """
        Delete a file from the store.

        Nothing is done if the file does not exist.
        """
        try:
            await self._s3_client().delete_object(Bucket=self._bucket, Key=key)
        except ClientError as e:
            raise FileStoreError("S3 delete failed") from e
        except BotoCoreError as e:
            raise FileStoreError("S3 delete failed") from e

    async def health_check(self) -> None:
        """
        Check the health of the store.

        raises FileStoreError if the store cannot be reached or the bucket is unavailable.
        """
        try:
            await self._s3_client().head_bucket(Bucket=self._bucket)
        except ClientError as e:
            raise FileStoreError("S3 health check failed") from e
        except BotoCoreError as e:
            raise FileStoreError("S3 health check failed") from e
