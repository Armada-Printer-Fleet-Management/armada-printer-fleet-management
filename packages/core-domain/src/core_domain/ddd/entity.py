from abc import ABC

from core_domain.ddd.typed_id import TypedId


class Entity[IdT: TypedId](ABC):  # noqa: B024 -- abstract by role; it has no abstract methods
    """Base for every entity: state plus the rules that change it, with no I/O.

    An entity's identity is its ID, so two instances with the same ID are equal whatever their
    other fields hold. Subclasses are declared with `@dataclass(eq=False)`; a plain `@dataclass`
    replaces this equality with field-by-field comparison and makes the entity unhashable."""

    id: IdT

    def __eq__(self, other: object) -> bool:
        return type(other) is type(self) and other.id == self.id

    def __hash__(self) -> int:
        return hash(self.id)
