import functools
import inspect
from abc import ABC
from collections.abc import Callable

from google.protobuf.message import Message
from proto_utils import message_to_dict

PROTO_RESPONSE_MARKER = "_proto_response"


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
