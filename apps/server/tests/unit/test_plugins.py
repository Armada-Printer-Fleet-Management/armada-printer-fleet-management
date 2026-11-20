import re

import pytest
from identity_keycloak import KeycloakIdentityDirectory

from api.infrastructure.auth.identity_directory_settings import (
    KEYCLOAK_IDENTITY_BACKEND,
    IdentitySettings,
)
from api.infrastructure.auth.token_verifier_settings import OIDC_AUTH_BACKEND, AuthSettings
from api.infrastructure.content_asset.file_store_settings import (
    S3_FILE_STORE_BACKEND,
    FileStoreSettings,
)
from api.plugins import build_file_store, build_identity_directory, build_token_verifier


def test_an_unknown_file_store_backend_is_rejected() -> None:
    expected = f"FILE_STORE_BACKEND is 'nope'; expected one of: {S3_FILE_STORE_BACKEND}"

    with pytest.raises(ValueError, match=re.escape(expected)):
        build_file_store(FileStoreSettings(backend="nope"))


def test_an_unknown_auth_backend_is_rejected() -> None:
    expected = f"AUTH_BACKEND is 'nope'; expected one of: {OIDC_AUTH_BACKEND}"

    with pytest.raises(ValueError, match=re.escape(expected)):
        build_token_verifier(AuthSettings(backend="nope"))


@pytest.mark.parametrize("backend", [KEYCLOAK_IDENTITY_BACKEND, None], ids=["named", "default"])
def test_the_keycloak_identity_backend_is_built(
    backend: str | None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("IDENTITY_BASE_URL", "http://keycloak.example.test/auth")
    monkeypatch.setenv("IDENTITY_SERVICE_ACCOUNT_SECRET", "test-secret")
    monkeypatch.delenv("IDENTITY_BACKEND", raising=False)
    settings = IdentitySettings() if backend is None else IdentitySettings(backend=backend)

    assert isinstance(build_identity_directory(settings), KeycloakIdentityDirectory)
