from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum, auto
from typing import Self

from core_domain.ddd import Entity, RuleViolation
from core_domain.ids import AgreementId, UserId


class LegalDocumentKind(Enum):
    """Mirrors common.v1.LegalDocumentKind, without UNSPECIFIED, which is never valid."""

    LICENSE = auto()


@dataclass(frozen=True)
class LegalDocument:
    """One version of a legal document. A later effective date is a new version that every user
    must accept again."""

    kind: LegalDocumentKind
    effective_date: date


@dataclass(eq=False)
class Agreement(Entity[AgreementId]):
    """A user's acceptance of one version of a legal document. Its created_at is when they
    accepted."""

    id: AgreementId
    user_id: UserId
    kind: LegalDocumentKind
    effective_date: date
    created_at: datetime
    updated_at: datetime

    @classmethod
    def accept(
        cls,
        user_id: UserId,
        document: LegalDocument,
        current: Iterable[LegalDocument],
        now: datetime,
    ) -> Self:
        """Only the current version can be accepted, so a user is never recorded as agreeing to
        text they were not shown."""
        if document not in set(current):
            raise RuleViolation(
                f"The {document.kind.name.lower()} effective {document.effective_date} is not the"
                " current version"
            )
        return cls(AgreementId.new(), user_id, document.kind, document.effective_date, now, now)

    def covers(self, document: LegalDocument) -> bool:
        """Whether this acceptance still counts for the document's version."""
        return self.kind == document.kind and self.effective_date >= document.effective_date


def outstanding(
    current: Iterable[LegalDocument], agreements: Iterable[Agreement]
) -> list[LegalDocument]:
    """The current documents none of a user's agreements cover, which they must accept before
    using the software."""
    accepted = list(agreements)
    return [d for d in current if not any(a.covers(d) for a in accepted)]
