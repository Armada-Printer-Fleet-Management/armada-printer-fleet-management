from urllib.parse import quote

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from api.common.consts import S3_FILE_STORE_BACKEND


class FileStoreSettings(BaseSettings):
    """Which file store plugin this deployment uses. Each plugin reads its own settings."""

    model_config = SettingsConfigDict(env_prefix="FILE_STORE_")

    backend: str = S3_FILE_STORE_BACKEND


class S3FileStoreSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FILE_STORE_")

    endpoint_url: str
    region: str
    bucket: str
    access_key: str
    secret_key: SecretStr


class DatabaseSettings(BaseSettings):
    """Where the application database is. Read by the migrations and the dev seed."""

    model_config = SettingsConfigDict(env_prefix="DB_")

    host: str
    port: int = 5432
    name: str
    user: str
    password: SecretStr

    def url(self) -> str:
        # Quoted, because a generated password may hold characters a URL reserves.
        user = quote(self.user, safe="")
        password = quote(self.password.get_secret_value(), safe="")
        return f"postgresql+psycopg://{user}:{password}@{self.host}:{self.port}/{self.name}"


def database_url() -> str:
    # Fields are filled from DB_* environment variables, which pyright cannot see.
    return DatabaseSettings().url()  # pyright: ignore[reportCallIssue]
