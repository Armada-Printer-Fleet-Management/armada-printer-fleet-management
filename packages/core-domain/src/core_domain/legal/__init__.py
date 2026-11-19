"""The legal domain's entities and rules: which legal documents a user has accepted, shared by
every app that asks users to accept them."""

from core_domain.legal.entities import Agreement, LegalDocument, LegalDocumentKind, outstanding

__all__ = ["Agreement", "LegalDocument", "LegalDocumentKind", "outstanding"]
