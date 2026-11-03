from enum import StrEnum

from pydantic import HttpUrl, SecretStr, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class E2eRole(StrEnum):
    """The roles the suite signs in as, each with its own test user on the target."""

    STUDENT = "student"
    STAFF = "staff"


class E2eSettings(BaseSettings):
    """What the suite needs to know about its target. Every value comes from E2E_* environment
    variables, so nothing here can point the suite at a real deployment by default."""

    model_config = SettingsConfigDict(env_prefix="E2E_")

    server_url: HttpUrl
    auth_issuer: HttpUrl
    auth_client_id: str
    auth_client_secret: SecretStr
    student_username: str
    student_password: SecretStr
    staff_username: str
    staff_password: SecretStr

    def server(self) -> str:
        return str(self.server_url).rstrip("/")

    def token_url(self) -> str:
        return f"{str(self.auth_issuer).rstrip('/')}/protocol/openid-connect/token"

    def credentials(self, role: E2eRole) -> tuple[str, str]:
        match role:
            case E2eRole.STUDENT:
                return self.student_username, self.student_password.get_secret_value()
            case E2eRole.STAFF:
                return self.staff_username, self.staff_password.get_secret_value()


class E2eNotConfigured(Exception):
    def __init__(self, error: ValidationError) -> None:
        missing = sorted(
            f"E2E_{str(detail['loc'][0]).upper()}" for detail in error.errors() if detail["loc"]
        )
        super().__init__(
            f"The e2e suite is not configured: {', '.join(missing)}. "
            "apps/server/e2e/README.md lists every variable and where its value comes from."
        )


def load_settings() -> E2eSettings:
    try:
        # pydantic-settings fills the required fields from the environment.
        return E2eSettings()  # pyright: ignore[reportCallIssue]
    except ValidationError as error:
        raise E2eNotConfigured(error) from None
