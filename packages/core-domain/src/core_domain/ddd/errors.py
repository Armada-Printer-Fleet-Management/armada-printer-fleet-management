from core_domain.ddd.typed_id import TypedId


class DomainError(Exception):
    """Base for the errors a domain raises on purpose, and for a dependency it cannot reach. Each
    app maps these to its own transport's errors in one place, so every service reports them the
    same way."""


class EntityNotFound(DomainError):
    def __init__(self, entity_id: TypedId) -> None:
        super().__init__(f"{type(entity_id).__name__} {entity_id} was not found")
        self.entity_id = entity_id


class RuleViolation(DomainError):
    """An entity refused a change its rules do not allow."""


class InvalidValue(DomainError):
    """A value that can never be valid, whatever state the entity is in."""


class Unavailable(DomainError):
    """Something the domain depends on cannot be reached. The message names only the dependency,
    so it is safe to show a client; infrastructure chains the detailed cause."""

    def __init__(self, dependency: str) -> None:
        super().__init__(f"{dependency} is unavailable")


class InvalidPageToken(DomainError):
    """A page token that the repository did not issue."""

    def __init__(self) -> None:
        super().__init__("page_token is not valid")
