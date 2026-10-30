"""Builds the plugins each deployment chose in its configuration. Only api/main.py calls these,
handing each plugin to the infrastructure adapter that wraps it."""

from collections.abc import Callable, Mapping

from auth_oidc import OidcTokenVerifier
from plugin_api.file_store import FileStore
from plugin_api.token_verifier import TokenVerifier
from s3_file_store import S3FileStore

from api.common.consts import OIDC_AUTH_BACKEND, S3_FILE_STORE_BACKEND
from api.common.settings import (
    AuthOidcSettings,
    AuthSettings,
    FileStoreSettings,
    S3FileStoreSettings,
)


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


def _oidc_token_verifier() -> TokenVerifier:
    # Fields are filled from AUTH_* environment variables, which pyright cannot see.
    settings = AuthOidcSettings()  # pyright: ignore[reportCallIssue]
    return OidcTokenVerifier(
        issuer=settings.issuer,
        audience=settings.audience,
        jwks_url=settings.jwks_url,
        roles_claim=settings.roles_claim,
    )


FILE_STORE_BACKENDS: Mapping[str, Callable[[], FileStore]] = {
    S3_FILE_STORE_BACKEND: _s3_file_store,
}

AUTH_BACKENDS: Mapping[str, Callable[[], TokenVerifier]] = {
    OIDC_AUTH_BACKEND: _oidc_token_verifier,
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


def build_token_verifier(settings: AuthSettings) -> TokenVerifier:
    try:
        build = AUTH_BACKENDS[settings.backend]
    except KeyError:
        choices = ", ".join(sorted(AUTH_BACKENDS))
        raise ValueError(
            f"AUTH_BACKEND is {settings.backend!r}; expected one of: {choices}"
        ) from None
    return build()
