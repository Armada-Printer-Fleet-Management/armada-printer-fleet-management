"""KeycloakIdentityDirectory against a fake Keycloak served through httpx2.MockTransport, so every
Admin REST API call is answered without a network."""

import asyncio
import json
from collections.abc import Callable, Coroutine
from uuid import uuid4

import httpx2
import pytest
from plugin_api.identity_directory import AccountExistsError, IdentityDirectoryError, NewAccount

from identity_keycloak import KeycloakIdentityDirectory

BASE_URL = "http://localhost:8080/auth"
REALM = "test-realm"
CLIENT_ID = "test-client"
CLIENT_SECRET = "test-secret"
TOKEN_LIFETIME_SECONDS = 300
ADMIN_PATH = f"/auth/admin/realms/{REALM}"
TOKEN_PATH = f"/auth/realms/{REALM}/protocol/openid-connect/token"
ACCOUNT = NewAccount("person@example.com", "First", "Last", "staff")

type Handler = Callable[[httpx2.Request], httpx2.Response]


class FakeKeycloak:
    """One realm's users, roles and role mappings, behind the parts of the token endpoint and the
    Admin REST API the directory uses. Assign `on_create`, `on_map_role`, `on_delete`,
    `on_update`, `on_logout` or `on_admin` to answer differently. Set `omit_location` to create
    accounts without saying where, and `hidden_from_lookup` to keep them out of the user lookup.
    An update changes only the fields it sends, as Keycloak's does."""

    def __init__(self) -> None:
        self.roles = {"staff": {"id": "role-staff", "name": "staff"}}
        self.users: dict[str, dict[str, object]] = {}
        self.role_mappings: dict[str, list[str]] = {}
        self.issued_tokens: list[str] = []
        self.revoked_tokens: set[str] = set()
        self.now = 0.0
        self.on_create: Handler | None = None
        self.on_map_role: Handler | None = None
        self.on_delete: Handler | None = None
        self.on_update: Handler | None = None
        self.on_logout: Handler | None = None
        self.on_admin: Handler | None = None
        self.logged_out: list[str] = []
        self.omit_location = False
        self.hidden_from_lookup = False

    def handle(self, request: httpx2.Request) -> httpx2.Response:
        if request.url.path == TOKEN_PATH:
            return self._token(request)
        if self.on_admin is not None:
            return self.on_admin(request)
        bearer = request.headers.get("Authorization", "").removeprefix("Bearer ")
        if bearer not in self.issued_tokens or bearer in self.revoked_tokens:
            return httpx2.Response(401)
        return self._admin(request)

    def _token(self, request: httpx2.Request) -> httpx2.Response:
        form = dict(pair.split("=", 1) for pair in request.content.decode().split("&"))
        expected = {
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        }
        if form != expected:
            return httpx2.Response(401, json={"error": "unauthorized_client"})
        token = f"token-{len(self.issued_tokens) + 1}"
        self.issued_tokens.append(token)
        return httpx2.Response(
            200, json={"access_token": token, "expires_in": TOKEN_LIFETIME_SECONDS}
        )

    def _admin(self, request: httpx2.Request) -> httpx2.Response:
        path = request.url.path.removeprefix(ADMIN_PATH)
        match request.method, path.strip("/").split("/"):
            case "POST", ["users"]:
                if self.on_create is not None:
                    return self.on_create(request)
                user = json.loads(request.content)
                if any(existing["email"] == user["email"] for existing in self.users.values()):
                    return httpx2.Response(409)
                subject = str(uuid4())
                self.users[subject] = user
                if self.omit_location:
                    return httpx2.Response(201)
                return httpx2.Response(
                    201, headers={"Location": f"{BASE_URL}/admin/realms/{REALM}/users/{subject}"}
                )
            case "GET", ["users"]:
                exact = request.url.params.get("exact") == "true"
                username = request.url.params.get("username", "")
                found = [
                    {"id": subject, "username": user["username"]}
                    for subject, user in self.users.items()
                    if exact and user["username"] == username and not self.hidden_from_lookup
                ]
                return httpx2.Response(200, json=found)
            case "GET", ["roles", name]:
                role = self.roles.get(name)
                return httpx2.Response(404) if role is None else httpx2.Response(200, json=role)
            case "POST", ["users", subject, "role-mappings", "realm"]:
                if self.on_map_role is not None:
                    return self.on_map_role(request)
                names = [role["name"] for role in json.loads(request.content)]
                self.role_mappings.setdefault(subject, []).extend(names)
                return httpx2.Response(204)
            case "DELETE", ["users", subject]:
                if self.on_delete is not None:
                    return self.on_delete(request)
                if self.users.pop(subject, None) is None:
                    return httpx2.Response(404)
                self.role_mappings.pop(subject, None)
                return httpx2.Response(204)
            case "PUT", ["users", subject]:
                if self.on_update is not None:
                    return self.on_update(request)
                user = self.users.get(subject)
                if user is None:
                    return httpx2.Response(404)
                user.update(json.loads(request.content))
                return httpx2.Response(204)
            case "POST", ["users", subject, "logout"]:
                if self.on_logout is not None:
                    return self.on_logout(request)
                if subject not in self.users:
                    return httpx2.Response(404)
                self.logged_out.append(subject)
                return httpx2.Response(204)
            case _:
                return httpx2.Response(404)

    def directory(self, client_secret: str = CLIENT_SECRET) -> KeycloakIdentityDirectory:
        return KeycloakIdentityDirectory(
            base_url=BASE_URL,
            realm=REALM,
            client_id=CLIENT_ID,
            client_secret=client_secret,
            transport=httpx2.MockTransport(self.handle),
            clock=lambda: self.now,
        )


type Use[T] = Callable[[KeycloakIdentityDirectory], Coroutine[object, object, T]]


def run[T](keycloak: FakeKeycloak, use: Use[T], client_secret: str = CLIENT_SECRET) -> T:
    """Opens a directory over the fake Keycloak and runs `use` with it."""

    async def opened() -> T:
        async with keycloak.directory(client_secret) as directory:
            return await use(directory)

    return asyncio.run(opened())


def refused(request: httpx2.Request) -> httpx2.Response:
    raise httpx2.ConnectError("connection refused", request=request)


# Creating an account


def test_create_returns_the_subject_keycloak_assigned() -> None:
    keycloak = FakeKeycloak()

    subject = run(keycloak, lambda directory: directory.create_account(ACCOUNT))

    assert list(keycloak.users) == [subject]


def test_create_sends_the_email_as_username_with_both_names_enabled() -> None:
    keycloak = FakeKeycloak()

    subject = run(keycloak, lambda directory: directory.create_account(ACCOUNT))

    assert keycloak.users[subject] == {
        "username": "person@example.com",
        "email": "person@example.com",
        "firstName": "First",
        "lastName": "Last",
        "enabled": True,
    }


def test_create_gives_the_account_its_realm_role() -> None:
    keycloak = FakeKeycloak()

    subject = run(keycloak, lambda directory: directory.create_account(ACCOUNT))

    assert keycloak.role_mappings[subject] == ["staff"]


def test_an_account_created_without_its_location_is_found_by_username() -> None:
    keycloak = FakeKeycloak()
    keycloak.omit_location = True

    subject = run(keycloak, lambda directory: directory.create_account(ACCOUNT))

    assert list(keycloak.users) == [subject]
    assert keycloak.role_mappings[subject] == ["staff"]


# Refusing to create an account


def test_an_existing_email_is_refused_as_account_exists() -> None:
    keycloak = FakeKeycloak()
    run(keycloak, lambda directory: directory.create_account(ACCOUNT))

    with pytest.raises(AccountExistsError):
        run(keycloak, lambda directory: directory.create_account(ACCOUNT))


def test_any_other_refusal_to_create_is_a_directory_error() -> None:
    keycloak = FakeKeycloak()
    keycloak.on_create = lambda _: httpx2.Response(400, json={"errorMessage": "invalid"})

    with pytest.raises(IdentityDirectoryError) as raised:
        run(keycloak, lambda directory: directory.create_account(ACCOUNT))

    assert not isinstance(raised.value, AccountExistsError)


def test_an_account_keycloak_cannot_find_after_creating_is_a_directory_error() -> None:
    keycloak = FakeKeycloak()
    keycloak.omit_location = True
    keycloak.hidden_from_lookup = True

    with pytest.raises(IdentityDirectoryError):
        run(keycloak, lambda directory: directory.create_account(ACCOUNT))


def _forget_roles(keycloak: FakeKeycloak) -> None:
    keycloak.roles.clear()


def _refuse_role_mapping(keycloak: FakeKeycloak) -> None:
    keycloak.on_map_role = lambda _: httpx2.Response(500)


@pytest.mark.parametrize(
    "break_keycloak",
    [_forget_roles, _refuse_role_mapping],
    ids=["unknown role", "role mapping refused"],
)
def test_a_role_that_cannot_be_given_removes_the_new_account(
    break_keycloak: Callable[[FakeKeycloak], None],
) -> None:
    keycloak = FakeKeycloak()
    break_keycloak(keycloak)

    with pytest.raises(IdentityDirectoryError):
        run(keycloak, lambda directory: directory.create_account(ACCOUNT))

    assert keycloak.users == {}


def test_a_failed_clean_up_still_reports_why_the_create_failed() -> None:
    keycloak = FakeKeycloak()
    keycloak.on_map_role = lambda _: httpx2.Response(500)
    keycloak.on_delete = lambda _: httpx2.Response(503)

    with pytest.raises(IdentityDirectoryError, match="refused the role"):
        run(keycloak, lambda directory: directory.create_account(ACCOUNT))


def test_an_unreachable_keycloak_is_a_directory_error() -> None:
    keycloak = FakeKeycloak()
    keycloak.on_admin = refused

    with pytest.raises(IdentityDirectoryError):
        run(keycloak, lambda directory: directory.create_account(ACCOUNT))


# The admin token


def test_a_token_is_reused_until_it_nearly_expires_then_renewed() -> None:
    keycloak = FakeKeycloak()

    async def use(directory: KeycloakIdentityDirectory) -> None:
        await directory.create_account(ACCOUNT)
        keycloak.now = TOKEN_LIFETIME_SECONDS - 60
        await directory.delete_account("some-subject")
        assert len(keycloak.issued_tokens) == 1
        keycloak.now = TOKEN_LIFETIME_SECONDS
        await directory.delete_account("some-subject")

    run(keycloak, use)

    assert len(keycloak.issued_tokens) == 2


def test_a_refused_token_is_renewed_and_the_request_retried_once() -> None:
    keycloak = FakeKeycloak()

    async def use(directory: KeycloakIdentityDirectory) -> str:
        await directory.delete_account("some-subject")
        keycloak.revoked_tokens.update(keycloak.issued_tokens)
        return await directory.create_account(ACCOUNT)

    subject = run(keycloak, use)

    assert list(keycloak.users) == [subject]
    assert len(keycloak.issued_tokens) == 2


def test_wrong_client_credentials_fail_the_health_check() -> None:
    with pytest.raises(IdentityDirectoryError):
        run(FakeKeycloak(), lambda directory: directory.health_check(), client_secret="wrong")


# Deleting an account


def test_delete_removes_the_account() -> None:
    keycloak = FakeKeycloak()

    async def use(directory: KeycloakIdentityDirectory) -> None:
        await directory.delete_account(await directory.create_account(ACCOUNT))

    run(keycloak, use)

    assert keycloak.users == {}


def test_deleting_an_account_that_does_not_exist_succeeds() -> None:
    run(FakeKeycloak(), lambda directory: directory.delete_account(str(uuid4())))


def test_a_refused_deletion_is_a_directory_error() -> None:
    keycloak = FakeKeycloak()
    keycloak.on_delete = lambda _: httpx2.Response(403)

    with pytest.raises(IdentityDirectoryError):
        run(keycloak, lambda directory: directory.delete_account(str(uuid4())))


# Enabling and disabling an account


def change_access_after_create(keycloak: FakeKeycloak, enabled: bool) -> str:
    async def use(directory: KeycloakIdentityDirectory) -> str:
        subject = await directory.create_account(ACCOUNT)
        if enabled:
            await directory.enable_account(subject)
        else:
            await directory.disable_account(subject)
        return subject

    return run(keycloak, use)


def test_disable_disables_the_account_and_ends_its_sessions() -> None:
    keycloak = FakeKeycloak()

    subject = change_access_after_create(keycloak, enabled=False)

    assert keycloak.users[subject]["enabled"] is False
    assert keycloak.logged_out == [subject]


def test_disable_keeps_the_rest_of_the_account() -> None:
    keycloak = FakeKeycloak()

    subject = change_access_after_create(keycloak, enabled=False)

    assert keycloak.users[subject]["email"] == ACCOUNT.email
    assert keycloak.role_mappings[subject] == [ACCOUNT.role]


def test_enable_enables_the_account_without_ending_sessions() -> None:
    keycloak = FakeKeycloak()

    async def use(directory: KeycloakIdentityDirectory) -> str:
        subject = await directory.create_account(ACCOUNT)
        await directory.disable_account(subject)
        keycloak.logged_out.clear()
        await directory.enable_account(subject)
        return subject

    subject = run(keycloak, use)

    assert keycloak.users[subject]["enabled"] is True
    assert keycloak.logged_out == []


def test_disabling_an_account_that_does_not_exist_succeeds() -> None:
    run(FakeKeycloak(), lambda directory: directory.disable_account(str(uuid4())))


def test_disabling_an_account_whose_sessions_are_already_gone_succeeds() -> None:
    keycloak = FakeKeycloak()
    keycloak.on_logout = lambda _: httpx2.Response(404)

    subject = change_access_after_create(keycloak, enabled=False)

    assert keycloak.users[subject]["enabled"] is False


def test_enabling_an_account_that_does_not_exist_is_a_directory_error() -> None:
    with pytest.raises(IdentityDirectoryError):
        run(FakeKeycloak(), lambda directory: directory.enable_account(str(uuid4())))


@pytest.mark.parametrize("enabled", [True, False])
def test_a_refused_update_is_a_directory_error(enabled: bool) -> None:
    keycloak = FakeKeycloak()
    keycloak.on_update = lambda _: httpx2.Response(403)

    with pytest.raises(IdentityDirectoryError):
        change_access_after_create(keycloak, enabled)


def test_a_refused_logout_is_a_directory_error() -> None:
    keycloak = FakeKeycloak()
    keycloak.on_logout = lambda _: httpx2.Response(403)

    with pytest.raises(IdentityDirectoryError):
        change_access_after_create(keycloak, enabled=False)
