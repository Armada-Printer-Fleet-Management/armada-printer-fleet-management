# TEMP stub: the desktop has no sign-in yet, so the server cannot tell who is accepting. Until it
# can, each Windows user's acceptance of the legal documents is kept in a file beside the settings,
# under the ID in armada_infrastructure/temp_user.py, and the shared rules are applied here.
# Filling it in: once desktop sign-in exists, armada_app/composition.py hands AgreementService
# ApplicationServerAgreements instead, and this file and temp_user.py are deleted.
import json
from collections.abc import Callable, Iterable
from datetime import date, datetime
from pathlib import Path
from typing import cast
from uuid import UUID

from core_domain.ddd import EntityNotFound
from core_domain.ids import AgreementId, UserId
from core_domain.legal import Agreement, LegalDocument, LegalDocumentKind, outstanding

from armada_domains.legal.repository import AgreementRepository


class LocalAgreements(AgreementRepository):
    """This Windows user's agreements, in a JSON file. A damaged file counts as none accepted,
    which only asks the user to accept again."""

    def __init__(
        self,
        path: Path,
        documents: Iterable[LegalDocument],
        clock: Callable[[], datetime],
    ) -> None:
        self._path = path
        self._documents = list(documents)
        self._clock = clock

    def get(self, entity_id: AgreementId) -> Agreement:
        for agreement in self._load():
            if agreement.id == entity_id:
                return agreement
        raise EntityNotFound(entity_id)

    def outstanding(self, user_id: UserId) -> list[LegalDocument]:
        mine = [agreement for agreement in self._load() if agreement.user_id == user_id]
        return outstanding(self._documents, mine)

    def request_accept(self, user_id: UserId, document: LegalDocument) -> Agreement:
        agreement = Agreement.accept(user_id, document, self._documents, self._clock())
        self._save([*self._load(), agreement])
        return agreement

    def _load(self) -> list[Agreement]:
        if not self._path.is_file():
            return []
        try:
            rows = cast(list[dict[str, str]], json.loads(self._path.read_text(encoding="utf-8")))
            return [_from_row(row) for row in rows]
        except (ValueError, KeyError, TypeError):
            return []

    def _save(self, agreements: list[Agreement]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        rows = [_to_row(agreement) for agreement in agreements]
        self._path.write_text(json.dumps(rows, indent=2), encoding="utf-8")


def _to_row(agreement: Agreement) -> dict[str, str]:
    return {
        "id": str(agreement.id.value),
        "user_id": str(agreement.user_id.value),
        "kind": agreement.kind.name,
        "effective_date": agreement.effective_date.isoformat(),
        "created_at": agreement.created_at.isoformat(),
    }


def _from_row(row: dict[str, str]) -> Agreement:
    accepted = datetime.fromisoformat(row["created_at"])
    return Agreement(
        id=AgreementId(UUID(row["id"])),
        user_id=UserId(UUID(row["user_id"])),
        kind=LegalDocumentKind[row["kind"]],
        effective_date=date.fromisoformat(row["effective_date"]),
        created_at=accepted,
        updated_at=accepted,
    )
