from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

KEYCLOAK_IDENTITY_BACKEND = "keycloak"


class IdentitySettings(BaseSettings):
    """Which identity directory plugin creates sign-in accounts. Each plugin reads its own
    settings."""

    model_config = SettingsConfigDict(env_prefix="IDENTITY_")

    backend: str = KEYCLOAK_IDENTITY_BACKEND


class IdentityKeycloakSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="IDENTITY_")

    base_url: str
    realm: str = "armada"
    client_id: str = "armada-server"
    service_account_secret: SecretStr
