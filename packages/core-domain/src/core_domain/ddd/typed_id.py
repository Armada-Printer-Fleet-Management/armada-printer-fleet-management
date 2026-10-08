from dataclasses import dataclass
from typing import Self
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class TypedId:
    """Base for every entity ID. Each entity subclasses it once, and sibling subclasses are
    distinct types: passing a printer's ID where a print job's belongs is a pyright error, and
    the two never compare equal even when they hold the same UUID."""

    value: UUID

    @classmethod
    def new(cls) -> Self:
        return cls(uuid4())

    @classmethod
    def parse(cls, text: str) -> Self:
        """Raises ValueError if text is not a UUID."""
        return cls(UUID(text))

    def __str__(self) -> str:
        return str(self.value)
