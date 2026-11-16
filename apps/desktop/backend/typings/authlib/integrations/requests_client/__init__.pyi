from requests import Session

class OAuth2Session(Session):
    def __init__(
        self,
        client_id: str | None = None,
        *,
        scope: str | None = None,
        redirect_uri: str | None = None,
        code_challenge_method: str | None = None,
        token_endpoint: str | None = None,
        default_timeout: float | None = None,
    ) -> None: ...
    @property
    def token(self) -> dict[str, object] | None: ...
    def create_authorization_url(
        self, url: str, state: str | None = None, code_verifier: str | None = None
    ) -> tuple[str, str]: ...
    def fetch_token(
        self,
        url: str | None = None,
        *,
        authorization_response: str,
        code_verifier: str,
        state: str,
    ) -> dict[str, object]: ...
    def ensure_active_token(self, token: dict[str, object] | None = None) -> bool | None: ...
