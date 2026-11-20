from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from api.common.consts import API_PREFIX
from api.infrastructure.dev_data import STUB_STAFF_ID, stub_users
from tests.fake_app import FakeApp, fake_services
from tests.fakes import MemoryIdentityDirectory
from tests.rpc import Json, id_json, post
from tests.samples import NOW

_USERS = f"{API_PREFIX}/server.v1.UserService"
_STAFF = next(user for user in stub_users() if user.id == STUB_STAFF_ID)
_NEW_USER: Json = {
    "email": "  New.Person@Example.com ",
    "firstName": "New",
    "lastName": "Person",
    "role": "USER_ROLE_STUDENT",
}


def _timestamp(days_from_now: int) -> str:
    return (NOW + timedelta(days=days_from_now)).strftime("%Y-%m-%dT%H:%M:%SZ")


# GetUser


def test_get_user_returns_the_user(client: TestClient) -> None:
    body = post(client, f"{_USERS}/GetUser", {"userId": id_json(STUB_STAFF_ID)})

    assert body["user"]["id"] == id_json(STUB_STAFF_ID)
    assert body["user"]["email"] == _STAFF.email
    assert body["user"]["role"] == "USER_ROLE_STAFF"


def test_get_user_reports_an_unknown_id(client: TestClient) -> None:
    unknown = "00000000-0000-4000-8000-0000000000ff"

    body = post(client, f"{_USERS}/GetUser", {"userId": {"value": unknown}}, 404)

    assert body["code"] == "not_found"


@pytest.mark.parametrize(
    "request_body", [{}, {"userId": {"value": "not-a-uuid"}}], ids=["missing", "malformed"]
)
def test_get_user_refuses_a_user_id_that_is_not_a_uuid(
    client: TestClient, request_body: Json
) -> None:
    body = post(client, f"{_USERS}/GetUser", request_body, 400)

    assert body == {"code": "invalid_argument", "message": "user_id must be a UUID"}


# CreateUser


def test_create_user_returns_the_new_active_user(client: TestClient) -> None:
    body = post(client, f"{_USERS}/CreateUser", _NEW_USER)

    user = body["user"]
    assert user["email"] == "new.person@example.com"
    assert (user["firstName"], user["lastName"]) == ("New", "Person")
    assert user["role"] == "USER_ROLE_STUDENT"
    assert user["status"] == "USER_STATUS_ACTIVE"
    assert "expiresAt" not in user


def test_create_user_keeps_a_guests_expiry(client: TestClient) -> None:
    guest = {**_NEW_USER, "role": "USER_ROLE_GUEST", "expiresAt": _timestamp(1)}

    body = post(client, f"{_USERS}/CreateUser", guest)

    assert body["user"]["expiresAt"] == _timestamp(1)


def test_create_user_requires_a_role(client: TestClient) -> None:
    body = post(client, f"{_USERS}/CreateUser", {**_NEW_USER, "role": "USER_ROLE_UNSPECIFIED"}, 400)

    assert body == {"code": "invalid_argument", "message": "role must be set"}


def test_create_user_reports_a_user_the_rules_refuse(client: TestClient) -> None:
    guest_without_expiry = {**_NEW_USER, "role": "USER_ROLE_GUEST"}

    body = post(client, f"{_USERS}/CreateUser", guest_without_expiry, 400)

    assert body["code"] == "failed_precondition"


def test_create_user_reports_an_email_already_in_use(client: TestClient) -> None:
    body = post(client, f"{_USERS}/CreateUser", {**_NEW_USER, "email": _STAFF.email}, 409)

    assert body == {"code": "already_exists", "message": "A user with this email already exists"}


def test_create_user_reports_an_identity_provider_outage(fake_app: FakeApp) -> None:
    directory = MemoryIdentityDirectory()
    directory.healthy = False
    client = fake_app(fake_services(identity_directory=directory))

    body = post(client, f"{_USERS}/CreateUser", _NEW_USER, 503)

    assert body == {"code": "unavailable", "message": "identity provider is unavailable"}
