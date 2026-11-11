from datetime import UTC, date, datetime

import pytest

from core_domain.ddd import RuleViolation
from core_domain.ids import UserId
from core_domain.legal import Agreement, LegalDocument, LegalDocumentKind

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
