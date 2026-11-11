import pytest
from core_domain.ids import UserId
from fastapi.testclient import TestClient

from api.common.consts import API_PREFIX
from tests.rpc import Json, id_json, post

SERVICE = f"{API_PREFIX}/server.v1.AgreementService"
TERMS = "LEGAL_DOCUMENT_KIND_TERMS_OF_SERVICE"
PRIVACY = "LEGAL_DOCUMENT_KIND_PRIVACY_POLICY"


def outstanding(client: TestClient, user: UserId) -> list[Json]:
    body = post(client, f"{SERVICE}/ListOutstandingLegalDocuments", {"userId": id_json(user)})
    documents: list[Json] = body.get("legalDocuments", [])
    return documents


def accept(
    client: TestClient, user: UserId, kind: str, effective_date: str, expect: int = 200
) -> Json:
    body = {"userId": id_json(user), "kind": kind, "effectiveDate": effective_date}
    return post(client, f"{SERVICE}/AcceptAgreement", body, expect)


def test_a_new_user_must_accept_the_terms_and_privacy_policy_but_not_the_licence(
    client: TestClient,
) -> None:
    kinds = {document["kind"] for document in outstanding(client, UserId.new())}
    assert kinds == {TERMS, PRIVACY}


def test_nothing_is_outstanding_straight_after_accepting(client: TestClient) -> None:
    user = UserId.new()
    for document in outstanding(client, user):
        accept(client, user, document["kind"], document["effectiveDate"])

    assert outstanding(client, user) == []


@pytest.mark.parametrize(
    ("kind", "effective_date"),
    [("LEGAL_DOCUMENT_KIND_UNSPECIFIED", "2026-11-16"), (TERMS, "16-11-2026")],
    ids=["unspecified kind", "date not YYYY-MM-DD"],
)
def test_accept_refuses_an_invalid_document(
    client: TestClient, kind: str, effective_date: str
) -> None:
    body = accept(client, UserId.new(), kind, effective_date, expect=400)
    assert body["code"] == "invalid_argument"


def test_accept_refuses_a_version_that_is_not_current(client: TestClient) -> None:
    body = accept(client, UserId.new(), TERMS, "2020-01-01", expect=400)
    assert body["code"] == "failed_precondition"
