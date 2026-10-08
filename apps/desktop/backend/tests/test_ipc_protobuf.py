"""Every IPC call must return a protobuf message through @proto_response."""

import importlib
import inspect
import pkgutil
from collections.abc import Callable
from typing import get_type_hints

import pytest
from core_domain.ddd import EntityNotFound
from core_domain.ids import PrintJobId
from core_domain.print_job import PrintJob
from google.protobuf.message import Message

import armada_ipc
from armada_domains.print_job.service import PrintJobService
from armada_ipc import Ipc
from armada_ipc._base import PROTO_CALL_MARKER, PROTO_RESPONSE_MARKER, IpcModule

type Method = Callable[..., object]


def swept_modules() -> list[type[IpcModule]]:
    found: list[type[IpcModule]] = []
    for info in pkgutil.walk_packages(armada_ipc.__path__, f"{armada_ipc.__name__}."):
        module = importlib.import_module(info.name)
        for value in vars(module).values():
            if (
                inspect.isclass(value)
                and issubclass(value, IpcModule)
                and value is not IpcModule
                and value.__module__ == module.__name__
            ):
                found.append(value)
    return found


def swept_methods() -> dict[str, Method]:
    return {
        f"{cls.__module__}.{cls.__qualname__}.{name}": method
        for cls in swept_modules()
        for name, method in inspect.getmembers(cls, inspect.isfunction)
        if not name.startswith("_")
    }


def exposed(
    obj: object, path: str = "", seen: set[int] | None = None
) -> tuple[dict[str, Method], list[object]]:
    """Mirrors pywebview's get_functions, which decides what JS can call."""
    seen = set() if seen is None else seen
    methods: dict[str, Method] = {}
    objects: list[object] = [obj]
    if id(obj) in seen:
        return methods, []
    seen.add(id(obj))
    for name in dir(obj):
        if name.startswith("_"):
            continue
        attr = getattr(obj, name)
        if not getattr(attr, "_serializable", True):
            continue
        full_name = f"{path}.{name}" if path else name
        if inspect.ismethod(attr) or inspect.isfunction(attr):
            methods[full_name] = attr
        elif inspect.isclass(attr) or (not callable(attr) and hasattr(attr, "__module__")):
            child_methods, child_objects = exposed(attr, full_name, seen)
            methods.update(child_methods)
            objects.extend(child_objects)
    return methods, objects


class _NoPrintJobs:
    def get(self, entity_id: PrintJobId) -> PrintJob:
        raise EntityNotFound(entity_id)


EXPOSED_METHODS, EXPOSED_OBJECTS = exposed(Ipc(print_jobs=PrintJobService(_NoPrintJobs())))
SWEPT_METHODS = swept_methods()


def assert_proto_response(method: Method) -> None:
    assert getattr(method, PROTO_RESPONSE_MARKER, False), "missing @proto_response"
    return_type = get_type_hints(inspect.unwrap(method))["return"]
    assert inspect.isclass(return_type) and issubclass(return_type, Message), (
        f"returns {return_type!r}, not a protobuf message"
    )


def test_discovery_finds_ipc_calls() -> None:
    assert swept_modules()
    assert SWEPT_METHODS
    assert EXPOSED_METHODS


@pytest.mark.parametrize("module", swept_modules(), ids=lambda cls: cls.__qualname__)
def test_every_ipc_module_is_attached_to_ipc(module: type[IpcModule]) -> None:
    attached = {type(obj) for obj in EXPOSED_OBJECTS}
    assert module in attached, f"{module.__qualname__} is not attached to Ipc"


@pytest.mark.parametrize("name", list(SWEPT_METHODS))
def test_every_ipc_module_method_returns_protobuf(name: str) -> None:
    assert_proto_response(SWEPT_METHODS[name])


@pytest.mark.parametrize("name", list(EXPOSED_METHODS))
def test_every_exposed_method_returns_protobuf(name: str) -> None:
    method = EXPOSED_METHODS[name]
    assert inspect.ismethod(method) and isinstance(method.__self__, IpcModule), (
        "IPC calls must live on an IpcModule"
    )
    assert_proto_response(method)


@pytest.mark.parametrize("name", list(SWEPT_METHODS))
def test_ipc_calls_with_input_take_one_request_message(name: str) -> None:
    """JS passes arguments positionally, so loose ones shift silently when one is added."""
    method = SWEPT_METHODS[name]
    takes_input = len(inspect.signature(inspect.unwrap(method)).parameters) > 1
    assert not takes_input or getattr(method, PROTO_CALL_MARKER, False), "use @proto_call"


@pytest.mark.parametrize("name", list(SWEPT_METHODS))
def test_proto_response_keeps_parameter_names_for_pywebview(name: str) -> None:
    method = SWEPT_METHODS[name]
    expected = list(inspect.signature(inspect.unwrap(method)).parameters)
    assert inspect.getfullargspec(method).args == expected
