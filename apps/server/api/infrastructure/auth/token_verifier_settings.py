from pydantic_settings import BaseSettings, SettingsConfigDict

OIDC_AUTH_BACKEND = "oidc"


class AuthSettings(BaseSettings):
    """Which token verifier plugin the application uses.  Each plugin reads its own settings."""

    model_config = SettingsConfigDict(env_prefix="AUTH_")

    backend: str = OIDC_AUTH_BACKEND
    enforce: bool = False


class AuthOidcSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AUTH_")

    issuer: str
    audience: str = "armada-server"
    jwks_url: str
    roles_claim: str = "realm_access.roles"
