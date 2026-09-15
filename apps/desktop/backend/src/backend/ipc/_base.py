from abc import ABC


class IpcModule(ABC):  # noqa: B024
    """Base class every concrete IPC module extends. Each subclass owns one
    capability and is exposed as its own namespace on the Ipc object --
    pywebview walks nested class instances automatically, so
    window.pywebview.api.<module_attr>.<method>() reaches it directly."""
