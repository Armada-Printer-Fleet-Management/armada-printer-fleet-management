from collections.abc import Generator
from contextlib import contextmanager
from typing import ClassVar

from connectrpc.code import Code
from connectrpc.errors import ConnectError
from core_domain.ddd import EntityNotFound, RuleViolation, TypedId, Unavailable
from google.protobuf.message import Message
from proto_utils import ProtoMapper


class ApplicationServerClient[IdT: TypedId, IdMessageT: Message]:
    """Base for the adapters that implement a domain's repository port over the application
    server's Connect services."""

    _id_message_type: ClassVar[type[Message]]

    def _id(self, entity_id: IdT) -> IdMessageT:
        # A ClassVar cannot use the class's type parameters, so each subclass sets the matching
        # message type and this narrows it back.
        return ProtoMapper.id_to_proto(self._id_message_type, entity_id)  # pyright: ignore[reportReturnType]

    @contextmanager
    def _server_errors_as_domain(self, entity_id: IdT | None = None) -> Generator[None]:
        """The inverse of the server's domain_errors_as_connect: its refusals and outages become
        the same domain errors here. Pass the entity_id of a call about one entity, so NOT_FOUND
        names it; anything else passes through."""
        try:
            yield
        except ConnectError as error:
            if error.code is Code.NOT_FOUND and entity_id is not None:
                raise EntityNotFound(entity_id) from error
            if error.code is Code.FAILED_PRECONDITION:
                raise RuleViolation(error.message) from error
            if error.code is Code.UNAVAILABLE:
                raise Unavailable("application server") from error
            raise
