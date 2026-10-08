import functools
import inspect
from abc import ABC
from collections.abc import Callable
from typing import Protocol

from google.protobuf.json_format import ParseDict
from google.protobuf.message import Message
from proto_utils import message_to_dict

PROTO_RESPONSE_MARKER = "_proto_response"
PROTO_CALL_MARKER = "_proto_call"


class IpcModule(ABC):  # noqa: B024
    """Base class every concrete IPC module extends. Each subclass owns one
    capability and is exposed as its own namespace on the Ipc object --
    pywebview walks nested class instances automatically, so
    window.pywebview.api.<module_attr>.<method>() reaches it directly."""


def proto_response[**P, M: Message](method: Callable[P, M]) -> Callable[P, dict[str, object]]:
    """Decorator to add to every IPC call."""

    @functools.wraps(method)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> dict[str, object]:
        return message_to_dict(method(*args, **kwargs))

    setattr(wrapper, "__signature__", inspect.signature(method))  # noqa: B010 -- pyright rejects assignment
    setattr(wrapper, PROTO_RESPONSE_MARKER, True)
    return wrapper


class _ProtoCall[RequestT: Message](Protocol):
    def __call__[OwnerT, ResponseT: Message](
        self, method: Callable[[OwnerT, RequestT], ResponseT], /
    ) -> Callable[[OwnerT, dict[str, object]], dict[str, object]]: ...


def proto_call[RequestT: Message](request_type: type[RequestT]) -> _ProtoCall[RequestT]:
    """Decorator for an IPC call that takes input: one request message in, one response message
    out, shaped like an RPC. The frontend sends the request as protobuf JSON."""

    def decorate[OwnerT, ResponseT: Message](
        method: Callable[[OwnerT, RequestT], ResponseT],
    ) -> Callable[[OwnerT, dict[str, object]], dict[str, object]]:
        @functools.wraps(method)
        def wrapper(owner: OwnerT, request: dict[str, object]) -> dict[str, object]:
            return message_to_dict(method(owner, ParseDict(request, request_type())))

        setattr(wrapper, "__signature__", inspect.signature(method))  # noqa: B010 -- pyright rejects assignment
        setattr(wrapper, PROTO_RESPONSE_MARKER, True)
        setattr(wrapper, PROTO_CALL_MARKER, True)
        return wrapper

    return decorate
