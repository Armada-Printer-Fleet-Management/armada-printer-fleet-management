import re

import pytest

from api.common.consts import OIDC_AUTH_BACKEND, S3_FILE_STORE_BACKEND
from api.common.settings import AuthSettings, FileStoreSettings
from api.plugins import build_file_store, build_token_verifier


def test_an_unknown_file_store_backend_is_rejected() -> None:
    expected = f"FILE_STORE_BACKEND is 'nope'; expected one of: {S3_FILE_STORE_BACKEND}"

    with pytest.raises(ValueError, match=re.escape(expected)):
        build_file_store(FileStoreSettings(backend="nope"))


def test_an_unknown_auth_backend_is_rejected() -> None:
    expected = f"AUTH_BACKEND is 'nope'; expected one of: {OIDC_AUTH_BACKEND}"

    with pytest.raises(ValueError, match=re.escape(expected)):
        build_token_verifier(AuthSettings(backend="nope"))
