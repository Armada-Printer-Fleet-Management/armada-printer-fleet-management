from abc import ABC, abstractmethod
from typing import Protocol

from core_domain.ddd.typed_id import TypedId


class ReadRepository[IdT: TypedId, EntityT](Protocol):
    """Loads entities. A client of an authoritative service uses only this, so a change it
    makes to an entity locally can never be persisted."""

    def get(self, entity_id: IdT) -> EntityT:
        """Raises EntityNotFound if there is no such entity."""
        ...


class Repository[IdT: TypedId, EntityT](ReadRepository[IdT, EntityT], Protocol):
    """Loads and persists entities."""

    def save(self, entity: EntityT) -> None: ...


class AsyncReadRepository[IdT: TypedId, EntityT](Protocol):
    """ReadRepository for async callers."""

    async def get(self, entity_id: IdT) -> EntityT:
        """Raises EntityNotFound if there is no such entity."""
        ...


class AsyncRepository[IdT: TypedId, EntityT](AsyncReadRepository[IdT, EntityT], Protocol):
    """Repository for async callers."""

    async def save(self, entity: EntityT) -> None: ...


# The abstract bases below are what new repository ports extend: an adapter must inherit its port,
# so a missing method fails when the adapter is constructed. Each still satisfies the matching
# protocol above, so change() and change_async() accept either.


class AbstractReadRepository[IdT: TypedId, EntityT](ABC):
    """ReadRepository as an abstract base."""

    @abstractmethod
    def get(self, entity_id: IdT) -> EntityT:
        """Raises EntityNotFound if there is no such entity."""


class AbstractRepository[IdT: TypedId, EntityT](AbstractReadRepository[IdT, EntityT]):
    """Repository as an abstract base."""

    @abstractmethod
    def save(self, entity: EntityT) -> None: ...


class AbstractAsyncReadRepository[IdT: TypedId, EntityT](ABC):
    """AsyncReadRepository as an abstract base."""

    @abstractmethod
    async def get(self, entity_id: IdT) -> EntityT:
        """Raises EntityNotFound if there is no such entity."""


class AbstractAsyncRepository[IdT: TypedId, EntityT](AbstractAsyncReadRepository[IdT, EntityT]):
    """AsyncRepository as an abstract base."""

    @abstractmethod
    async def save(self, entity: EntityT) -> None: ...
