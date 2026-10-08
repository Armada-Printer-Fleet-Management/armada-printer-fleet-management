from dataclasses import dataclass, field
from uuid import uuid4

import pytest

from core_domain.ddd import Entity, EntityNotFound, RuleViolation, TypedId, change


class AlphaId(TypedId):
    __slots__ = ()


class BetaId(TypedId):
    __slots__ = ()


@dataclass(eq=False)
class Alpha(Entity[AlphaId]):
    id: AlphaId
    count: int = 0

    def increment(self) -> None:
        if self.count >= 1:
            raise RuleViolation("already incremented")
        self.count += 1


@dataclass
class InMemory:
    saved: dict[AlphaId, Alpha] = field(default_factory=dict[AlphaId, Alpha])
    save_count: int = 0

    def get(self, entity_id: AlphaId) -> Alpha:
        if entity_id not in self.saved:
            raise EntityNotFound(entity_id)
        return self.saved[entity_id]

    def save(self, entity: Alpha) -> None:
        self.saved[entity.id] = entity
        self.save_count += 1


def test_ids_of_different_entities_never_compare_equal() -> None:
    value = uuid4()
    assert AlphaId(value) == AlphaId(value)
    assert AlphaId(value) != BetaId(value)


def test_ids_are_hashable_and_parse_uuids() -> None:
    entity_id = AlphaId.new()
    assert {entity_id: 1}[AlphaId.parse(str(entity_id))] == 1
    with pytest.raises(ValueError):
        AlphaId.parse("not-a-uuid")


def test_entities_are_equal_by_id_alone() -> None:
    entity_id = AlphaId.new()
    assert Alpha(entity_id, count=0) == Alpha(entity_id, count=5)
    assert Alpha(entity_id) != Alpha(AlphaId.new())
    assert len({Alpha(entity_id), Alpha(entity_id, count=1)}) == 1


def test_change_loads_applies_the_rule_and_saves() -> None:
    repository = InMemory()
    entity_id = AlphaId.new()
    repository.save(Alpha(entity_id))

    changed = change(repository, entity_id, Alpha.increment)

    assert changed.count == 1
    assert repository.get(entity_id).count == 1


def test_change_saves_nothing_when_the_rule_refuses() -> None:
    repository = InMemory()
    entity_id = AlphaId.new()
    repository.save(Alpha(entity_id, count=1))

    with pytest.raises(RuleViolation):
        change(repository, entity_id, Alpha.increment)
    assert repository.save_count == 1


def test_change_reports_a_missing_entity() -> None:
    with pytest.raises(EntityNotFound):
        change(InMemory(), AlphaId.new(), Alpha.increment)
