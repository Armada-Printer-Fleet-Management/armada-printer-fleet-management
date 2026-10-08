"""The generic DDD bases every domain is built on."""

from core_domain.ddd.entity import Entity
from core_domain.ddd.errors import DomainError, EntityNotFound, RuleViolation
from core_domain.ddd.repository import (
    AsyncReadRepository,
    AsyncRepository,
    ReadRepository,
    Repository,
)
from core_domain.ddd.service import Service, change, change_async
from core_domain.ddd.typed_id import TypedId

__all__ = [
    "AsyncReadRepository",
    "AsyncRepository",
    "DomainError",
    "Entity",
    "EntityNotFound",
    "ReadRepository",
    "Repository",
    "RuleViolation",
    "Service",
    "TypedId",
    "change",
    "change_async",
]
