from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Protocol
from uuid import UUID

from google.protobuf.message import Message


class ProtoId(Protocol):
    """Any id.v1 message."""

    value: str


class _DomainId(Protocol):
    @property
    def value(self) -> UUID: ...


class ProtoMapper[EntityT, MessageT: Message](ABC):
    """Converts one domain entity to and from its wire message. Each app implements one per entity,
    at its transport edge (an RPC handler, a Connect client adapter), because generated code is
    per app; the domain itself never sees protobuf.

    The typed-ID conversions are static so code that maps a lone ID, such as a request's
    print_job_id, uses them without a mapper instance."""

    @abstractmethod
    def to_proto(self, entity: EntityT) -> MessageT: ...

    @abstractmethod
    def to_entity(self, message: MessageT) -> EntityT:
        """Raises ValueError if the message cannot be a valid entity, such as a malformed ID."""
        ...

    @staticmethod
    def id_from_proto[IdT](id_type: Callable[[UUID], IdT], message: ProtoId) -> IdT:
        """Converts an id.v1 message to the domain's typed ID, e.g.
        `id_from_proto(PrintJobId, request.print_job_id)`. Raises ValueError if it holds no
        UUID, which includes an ID that was never set."""
        return id_type(UUID(message.value))

    @staticmethod
    def optional_id_from_proto[IdT](id_type: Callable[[UUID], IdT], message: ProtoId) -> IdT | None:
        """id_from_proto for a field that may be unset."""
        return ProtoMapper.id_from_proto(id_type, message) if message.value else None

    @staticmethod
    def id_to_proto[IdMessageT: Message](
        message_type: type[IdMessageT], domain_id: _DomainId
    ) -> IdMessageT:
        """Converts a domain typed ID to its id.v1 message, e.g.
        `id_to_proto(PrintJobIdPb, job.id)`."""
        return message_type(value=str(domain_id.value))

    @staticmethod
    def optional_id_to_proto[IdMessageT: Message](
        message_type: type[IdMessageT], domain_id: _DomainId | None
    ) -> IdMessageT | None:
        """id_to_proto for an ID that may be absent; None leaves the field unset."""
        return None if domain_id is None else ProtoMapper.id_to_proto(message_type, domain_id)
