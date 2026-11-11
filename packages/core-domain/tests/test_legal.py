from datetime import UTC, date, datetime

import pytest

from core_domain.ddd import RuleViolation
from core_domain.ids import UserId
from core_domain.legal import Agreement, LegalDocument, LegalDocumentKind, outstanding

NOW = datetime(2026, 11, 11, tzinfo=UTC)
USER = UserId.new()
CURRENT = LegalDocument(LegalDocumentKind.LICENSE, date(2026, 11, 11))


def test_accept_records_the_current_version() -> None:
    agreement = Agreement.accept(USER, CURRENT, [CURRENT], NOW)

    assert (agreement.user_id, agreement.kind, agreement.effective_date) == (
        USER,
        LegalDocumentKind.LICENSE,
        date(2026, 11, 11),
    )
    assert agreement.created_at == agreement.updated_at == NOW


def test_accept_refuses_a_version_that_is_not_current() -> None:
    stale = LegalDocument(LegalDocumentKind.LICENSE, date(2020, 1, 1))

    with pytest.raises(RuleViolation):
        Agreement.accept(USER, stale, [CURRENT], NOW)


LICENCE = LegalDocument(LegalDocumentKind.LICENSE, date(2026, 11, 11))
TERMS = LegalDocument(LegalDocumentKind.TERMS_OF_SERVICE, date(2026, 11, 16))
PRIVACY = LegalDocument(LegalDocumentKind.PRIVACY_POLICY, date(2026, 11, 16))


def test_a_licence_is_never_outstanding() -> None:
    assert not LICENCE.requires_acceptance()
    assert outstanding([LICENCE], []) == []


def test_terms_and_privacy_are_outstanding_until_accepted() -> None:
    current = [LICENCE, TERMS, PRIVACY]
    assert outstanding(current, []) == [TERMS, PRIVACY]

    accepted = [Agreement.accept(USER, document, current, NOW) for document in (TERMS, PRIVACY)]
    assert outstanding(current, accepted) == []


def test_a_new_version_asks_again() -> None:
    old_terms = LegalDocument(LegalDocumentKind.TERMS_OF_SERVICE, date(2026, 1, 1))
    accepted = Agreement.accept(USER, old_terms, [old_terms], NOW)

    assert outstanding([TERMS], [accepted]) == [TERMS]
