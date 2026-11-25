"""UserService against the real Postgres and Keycloak. Keycloak is not reset between tests, so each
test uses an email of its own."""

from collections.abc import Iterator
from uuid import uuid4

import httpx2
import pytest
from fastapi.testclient import TestClient

from api.common.consts import API_PREFIX
from tests.rpc import Json, post

_USERS = f"{API_PREFIX}/server.v1.UserService"


class KeycloakUsers:
    """Reads the armada realm's users as the server's own service account does."""

    def __init__(self, base_url: str, client_secret: str) -> None:
        self._admin_url = f"{base_url}/admin/realms/armada"
        token = httpx2.post(
            f"{base_url}/realms/armada/protocol/openid-connect/token",
            data={
                "grant_type": "client_credentials",
                "client_id": "armada-server",
                "client_secret": client_secret,
            },
        )
        token.raise_for_status()
        self._client = httpx2.Client(
            headers={"Authorization": f"Bearer {token.json()['access_token']}"}
        )

    def with_email(self, email: str) -> list[Json]:
        response = self._client.get(
            f"{self._admin_url}/users", params={"email": email, "exact": "true"}
        )
        response.raise_for_status()
        users: list[Json] = response.json()
        return users

    def realm_roles(self, subject: str) -> set[str]:
        response = self._client.get(f"{self._admin_url}/users/{subject}/role-mappings/realm")
        response.raise_for_status()
        return {role["name"] for role in response.json()}

    def close(self) -> None:
        self._client.close()


@pytest.fixture
def keycloak_users(stack_environment: dict[str, str]) -> Iterator[KeycloakUsers]:
    users = KeycloakUsers(
        stack_environment["IDENTITY_BASE_URL"], stack_environment["IDENTITY_SERVICE_ACCOUNT_SECRET"]
    )
    yield users
    users.close()


def new_user(role: str = "USER_ROLE_STAFF") -> Json:
    return {
        "email": f"user-{uuid4().hex[:12]}@example.com",
        "firstName": "First",
        "lastName": "Last",
        "role": role,
    }


@pytest.mark.parametrize(
    ("procedure", "body", "status"),
    [
        ("GetUser", {"userId": {"value": str(uuid4())}}, 404),
        ("CreateUser", {}, 400),
        ("ListUsers", {"page": {"pageToken": "nope"}}, 400),
        ("TransitionUserStatus", {"userId": {"value": str(uuid4())}, "suspend": {}}, 404),
    ],
    ids=["GetUser", "CreateUser", "ListUsers", "TransitionUserStatus"],
)
def test_rpc_is_mounted_on_the_app(
    app_client: TestClient, procedure: str, body: Json, status: int
) -> None:
    response = app_client.post(f"{_USERS}/{procedure}", json=body)

    assert response.status_code == status, response.text
    assert response.json()["code"] != "unimplemented"


def test_a_created_user_is_stored_and_has_a_keycloak_account_with_its_role(
    app_client: TestClient, keycloak_users: KeycloakUsers
) -> None:
    request = new_user()

    created = post(app_client, f"{_USERS}/CreateUser", request)["user"]
    fetched = post(app_client, f"{_USERS}/GetUser", {"userId": created["id"]})["user"]

    assert fetched == created
    [account] = keycloak_users.with_email(request["email"])
    assert (account["firstName"], account["lastName"]) == ("First", "Last")
    assert "staff" in keycloak_users.realm_roles(account["id"])


def test_a_duplicate_email_is_refused_and_leaves_one_account(
    app_client: TestClient, keycloak_users: KeycloakUsers
) -> None:
    request = new_user()
    post(app_client, f"{_USERS}/CreateUser", request)

    body = post(app_client, f"{_USERS}/CreateUser", request, 409)

    assert body["code"] == "already_exists"
    assert len(keycloak_users.with_email(request["email"])) == 1


def test_a_user_the_rules_refuse_leaves_no_keycloak_account(
    app_client: TestClient, keycloak_users: KeycloakUsers
) -> None:
    guest_without_expiry = new_user("USER_ROLE_GUEST")

    post(app_client, f"{_USERS}/CreateUser", guest_without_expiry, 400)

    assert keycloak_users.with_email(guest_without_expiry["email"]) == []


def _transition(client: TestClient, user_id: Json, action: str) -> Json:
    body = post(client, f"{_USERS}/TransitionUserStatus", {"userId": user_id, action: {}})
    user: Json = body["user"]
    return user


def test_deleting_a_user_disables_their_account_and_reactivating_enables_it(
    app_client: TestClient, keycloak_users: KeycloakUsers
) -> None:
    request = new_user()
    created = post(app_client, f"{_USERS}/CreateUser", request)["user"]

    deleted = _transition(app_client, created["id"], "delete")
    [disabled] = keycloak_users.with_email(request["email"])
    reactivated = _transition(app_client, created["id"], "reactivate")
    [enabled] = keycloak_users.with_email(request["email"])

    assert deleted["status"] == "USER_STATUS_DELETED"
    assert disabled["enabled"] is False
    assert reactivated["status"] == "USER_STATUS_ACTIVE"
    assert enabled["enabled"] is True
    assert enabled["id"] == disabled["id"]
