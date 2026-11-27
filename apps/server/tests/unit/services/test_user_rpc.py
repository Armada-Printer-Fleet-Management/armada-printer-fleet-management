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


# ListUsers


def test_list_users_returns_every_user_a_page_at_a_time(client: TestClient) -> None:
    # One short of every user, so the last one is left for the second page.
    page_size = len(stub_users()) - 1
    first = post(client, f"{_USERS}/ListUsers", {"page": {"pageSize": page_size}})
    token = first["page"]["nextPageToken"]
    second = post(
        client, f"{_USERS}/ListUsers", {"page": {"pageSize": page_size, "pageToken": token}}
    )

    ids = [user["id"] for user in first["users"] + second["users"]]
    assert sorted(ids, key=str) == sorted([id_json(user.id) for user in stub_users()], key=str)
    assert "nextPageToken" not in second.get("page", {})


def test_list_users_includes_deleted_users(client: TestClient) -> None:
    user = post(client, f"{_USERS}/CreateUser", _NEW_USER)["user"]
    _transition(client, user["id"], "delete")

    body = post(client, f"{_USERS}/ListUsers", {})

    statuses = {listed["id"]["value"]: listed["status"] for listed in body["users"]}
    assert statuses[user["id"]["value"]] == "USER_STATUS_DELETED"


def test_list_users_rejects_a_bad_page_token(client: TestClient) -> None:
    body = post(client, f"{_USERS}/ListUsers", {"page": {"pageToken": "nope"}}, 400)

    assert body["code"] == "invalid_argument"


# TransitionUserStatus


def _transition(client: TestClient, user_id: Json, action: str, expect: int = 200) -> Json:
    return post(
        client,
        f"{_USERS}/TransitionUserStatus",
        {"userId": user_id, action: {}},
        expect,
    )


@pytest.mark.parametrize(
    ("setup", "action", "status"),
    [
        (None, "suspend", "USER_STATUS_SUSPENDED"),
        (None, "delete", "USER_STATUS_DELETED"),
        ("suspend", "reactivate", "USER_STATUS_ACTIVE"),
    ],
    ids=["suspend", "delete", "reactivate"],
)
def test_transition_user_status_returns_the_changed_user(
    client: TestClient, setup: str | None, action: str, status: str
) -> None:
    user = post(client, f"{_USERS}/CreateUser", _NEW_USER)["user"]
    if setup is not None:
        _transition(client, user["id"], setup)

    body = _transition(client, user["id"], action)

    assert body["user"]["id"] == user["id"]
    assert body["user"]["status"] == status
    assert ("deletedAt" in body["user"]) is (action == "delete")


def test_transition_user_status_requires_an_action(client: TestClient) -> None:
    body = post(client, f"{_USERS}/TransitionUserStatus", {"userId": id_json(STUB_STAFF_ID)}, 400)

    assert body == {"code": "invalid_argument", "message": "action must be set"}


def test_transition_user_status_reports_a_transition_the_rules_refuse(
    client: TestClient,
) -> None:
    body = _transition(client, id_json(STUB_STAFF_ID), "reactivate", 400)

    assert body["code"] == "failed_precondition"


def test_transition_user_status_reports_an_unknown_id(client: TestClient) -> None:
    unknown = {"value": "00000000-0000-4000-8000-0000000000ff"}

    body = _transition(client, unknown, "suspend", 404)

    assert body["code"] == "not_found"


@pytest.mark.parametrize("user_id", [None, {"value": "not-a-uuid"}], ids=["missing", "malformed"])
def test_transition_user_status_refuses_a_user_id_that_is_not_a_uuid(
    client: TestClient, user_id: Json | None
) -> None:
    request_body: Json = {"suspend": {}} if user_id is None else {"userId": user_id, "suspend": {}}

    body = post(client, f"{_USERS}/TransitionUserStatus", request_body, 400)

    assert body == {"code": "invalid_argument", "message": "user_id must be a UUID"}


def test_transition_user_status_reports_an_identity_provider_outage(fake_app: FakeApp) -> None:
    directory = MemoryIdentityDirectory()
    client = fake_app(fake_services(identity_directory=directory))
    user = post(client, f"{_USERS}/CreateUser", _NEW_USER)["user"]
    directory.healthy = False

    body = _transition(client, user["id"], "suspend", 503)

    assert body == {"code": "unavailable", "message": "identity provider is unavailable"}


# TransitionUserRole


def _change_role(client: TestClient, user_id: Json, action: Json, expect: int = 200) -> Json:
    return post(client, f"{_USERS}/TransitionUserRole", {"userId": user_id, **action}, expect)


@pytest.mark.parametrize(
    ("action", "role", "directory_role"),
    [
        ({"makeGuest": {"expiresAt": _timestamp(1)}}, "USER_ROLE_GUEST", "guest"),
        ({"makeStaff": {}}, "USER_ROLE_STAFF", "staff"),
        ({"makeAdmin": {}}, "USER_ROLE_ADMIN", "admin"),
    ],
    ids=["guest", "staff", "admin"],
)
def test_transition_user_role_returns_the_user_with_the_new_role(
    fake_app: FakeApp, action: Json, role: str, directory_role: str
) -> None:
    directory = MemoryIdentityDirectory()
    client = fake_app(fake_services(identity_directory=directory))
    user = post(client, f"{_USERS}/CreateUser", _NEW_USER)["user"]

    body = _change_role(client, user["id"], action)

    assert body["user"]["id"] == user["id"]
    assert body["user"]["role"] == role
    (subject,) = directory.accounts
    assert directory.accounts[subject].role == directory_role
    assert directory.sessions_ended == {subject}


def test_transition_user_role_makes_a_guest_a_student_and_clears_the_expiry(
    client: TestClient,
) -> None:
    guest = {**_NEW_USER, "role": "USER_ROLE_GUEST", "expiresAt": _timestamp(1)}
    user = post(client, f"{_USERS}/CreateUser", guest)["user"]

    body = _change_role(client, user["id"], {"makeStudent": {}})

    assert body["user"]["role"] == "USER_ROLE_STUDENT"
    assert "expiresAt" not in body["user"]


def test_transition_user_role_requires_an_action(client: TestClient) -> None:
    body = post(client, f"{_USERS}/TransitionUserRole", {"userId": id_json(STUB_STAFF_ID)}, 400)

    assert body == {"code": "invalid_argument", "message": "action must be set"}


@pytest.mark.parametrize("user_id", [None, {"value": "not-a-uuid"}], ids=["missing", "malformed"])
def test_transition_user_role_refuses_a_user_id_that_is_not_a_uuid(
    client: TestClient, user_id: Json | None
) -> None:
    request_body: Json = (
        {"makeStaff": {}} if user_id is None else {"userId": user_id, "makeStaff": {}}
    )

    body = post(client, f"{_USERS}/TransitionUserRole", request_body, 400)

    assert body == {"code": "invalid_argument", "message": "user_id must be a UUID"}


def test_transition_user_role_reports_an_unknown_id(client: TestClient) -> None:
    unknown = {"value": "00000000-0000-4000-8000-0000000000ff"}

    body = _change_role(client, unknown, {"makeStaff": {}}, 404)

    assert body["code"] == "not_found"


@pytest.mark.parametrize(
    "action",
    [{"makeStudent": {}}, {"makeGuest": {}}, {"makeGuest": {"expiresAt": _timestamp(-1)}}],
    ids=["same role", "guest without expiry", "guest with past expiry"],
)
def test_transition_user_role_reports_a_change_the_rules_refuse(
    fake_app: FakeApp, action: Json
) -> None:
    directory = MemoryIdentityDirectory()
    client = fake_app(fake_services(identity_directory=directory))
    user = post(client, f"{_USERS}/CreateUser", _NEW_USER)["user"]

    body = _change_role(client, user["id"], action, 400)

    assert body["code"] == "failed_precondition"
    (subject,) = directory.accounts
    assert directory.accounts[subject].role == "student"
    assert directory.sessions_ended == set()


def test_transition_user_role_reports_an_identity_provider_outage(fake_app: FakeApp) -> None:
    directory = MemoryIdentityDirectory()
    client = fake_app(fake_services(identity_directory=directory))
    user = post(client, f"{_USERS}/CreateUser", _NEW_USER)["user"]
    directory.healthy = False

    body = _change_role(client, user["id"], {"makeStaff": {}}, 503)

    assert body == {"code": "unavailable", "message": "identity provider is unavailable"}
    stored = post(client, f"{_USERS}/GetUser", {"userId": user["id"]})["user"]
    assert stored["role"] == "USER_ROLE_STUDENT"
