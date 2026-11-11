"""Check that every legal document matches its SHA-256 in organization.json.

Builds call this so that a changed licence, terms of service or privacy policy cannot ship under
the old effective date. Users accept a document by its effective date, so changed text without a
new date would never be shown to them again.

    python scripts/check_legal_documents.py

Standard library only.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
ORGANIZATION = ROOT / "packages" / "organization-info" / "organization.json"


class LegalDocumentsChanged(Exception):
    """A legal document no longer matches organization.json."""


def problems(root: pathlib.Path = ROOT) -> list[str]:
    """One line per legal document that is missing or whose text changed."""
    organization = json.loads(
        (root / ORGANIZATION.relative_to(ROOT)).read_text(encoding="utf-8")
    )
    found: list[str] = []
    for document in organization.get("legalDocuments", []):
        path = root / document["path"]
        if not path.is_file():
            found.append(f"{document['path']}: missing")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != document["sha256"]:
            found.append(f"{document['path']}: changed; its SHA-256 is now {actual}")
    return found


def check(root: pathlib.Path = ROOT) -> None:
    """Raises LegalDocumentsChanged, explaining what to update, when any document changed."""
    found = problems(root)
    if found:
        raise LegalDocumentsChanged(
            "Legal documents do not match packages/organization-info/organization.json:\n  "
            + "\n  ".join(found)
            + "\nFor each changed document, set effectiveDate to the day the new text takes "
            "effect and sha256 to the value above, so users are asked to accept it again."
        )


def main() -> int:
    try:
        check()
    except LegalDocumentsChanged as error:
        print(error, file=sys.stderr)
        return 1
    print("Legal documents match organization.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())