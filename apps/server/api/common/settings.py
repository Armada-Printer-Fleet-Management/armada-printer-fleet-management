from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class FileStoreSettings(BaseSettings):
    """Which file store plugin this deployment uses. Each plugin reads its own settings."""

    model_config = SettingsConfigDict(env_prefix="FILE_STORE_")

    backend: str = "s3"


class S3FileStoreSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FILE_STORE_")

    endpoint_url: str
    region: str
    bucket: str
    access_key: str
    secret_key: SecretStr
