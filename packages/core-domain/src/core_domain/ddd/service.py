from abc import ABC
from collections.abc import Callable

from core_domain.ddd.repository import AsyncRepository, Repository
from core_domain.ddd.typed_id import TypedId


class Service[RepositoryT](ABC):  # noqa: B024 -- abstract by role; it has no abstract methods
    """Base for every domain service, the public interface of a domain: one method per use case.
    Other code calls a domain only through its service."""

    def __init__(self, repository: RepositoryT) -> None:
        self._repository = repository


def change[IdT: TypedId, EntityT](
    repository: Repository[IdT, EntityT], entity_id: IdT, rule: Callable[[EntityT], None]
) -> EntityT:
    """The standard flow for a use case that changes an entity: load it, let it apply its own
    rule, persist it. A rule that refuses raises, and nothing is saved."""
    entity = repository.get(entity_id)
    rule(entity)
    repository.save(entity)
    return entity


async def change_async[IdT: TypedId, EntityT](
    repository: AsyncRepository[IdT, EntityT], entity_id: IdT, rule: Callable[[EntityT], None]
) -> EntityT:
    """`change` for async repositories."""
    entity = await repository.get(entity_id)
    rule(entity)
    await repository.save(entity)
    return entity
