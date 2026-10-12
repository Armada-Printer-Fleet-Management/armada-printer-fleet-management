"""Builds the plugins each deployment chose in its configuration. Only api/main.py calls these,
handing each plugin to the infrastructure adapter that wraps it."""

from collections.abc import Callable, Mapping

from plugin_api.file_store import FileStore
from s3_file_store import S3FileStore

from api.common.consts import S3_FILE_STORE_BACKEND
from api.common.settings import FileStoreSettings, S3FileStoreSettings


def _s3_file_store() -> FileStore:
    # Fields are filled from FILE_STORE_* environment variables, which pyright cannot see.
    settings = S3FileStoreSettings()  # pyright: ignore[reportCallIssue]
    return S3FileStore(
        endpoint_url=settings.endpoint_url,
        region_name=settings.region,
        bucket=settings.bucket,
        access_key=settings.access_key,
        secret_key=settings.secret_key.get_secret_value(),
    )


FILE_STORE_BACKENDS: Mapping[str, Callable[[], FileStore]] = {
    S3_FILE_STORE_BACKEND: _s3_file_store,
}


def build_file_store(settings: FileStoreSettings) -> FileStore:
    try:
        build = FILE_STORE_BACKENDS[settings.backend]
    except KeyError:
        choices = ", ".join(sorted(FILE_STORE_BACKENDS))
        raise ValueError(
            f"FILE_STORE_BACKEND is {settings.backend!r}; expected one of: {choices}"
        ) from None
    return build()
