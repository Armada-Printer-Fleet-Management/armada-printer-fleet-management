from core_domain.ddd.typed_id import TypedId


class DomainError(Exception):
    """Base for the errors a domain raises on purpose. Each app maps these to its own transport's
    errors in one place, so every service reports them the same way."""


class EntityNotFound(DomainError):
    def __init__(self, entity_id: TypedId) -> None:
        super().__init__(f"{type(entity_id).__name__} {entity_id} was not found")
        self.entity_id = entity_id


class RuleViolation(DomainError):
    """An entity refused a change its rules do not allow."""
