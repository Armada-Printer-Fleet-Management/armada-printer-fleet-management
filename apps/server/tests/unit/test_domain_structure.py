"""Every server domain has the same shape: a repository port and a service, over an entity that
lives once in core_domain."""

import ast
import importlib
import importlib.util
import inspect
from pathlib import Path

import pytest
from core_domain.ddd import Service

import api.domains

DOMAINS = Path(api.domains.__file__).parent
NAMES = sorted(p.name for p in DOMAINS.iterdir() if p.is_dir() and p.name != "__pycache__")


def test_domains_are_found() -> None:
    assert NAMES


@pytest.mark.parametrize("domain", NAMES)
def test_domain_has_a_repository_and_a_service(domain: str) -> None:
    for part in ("repository.py", "service.py"):
        assert (DOMAINS / domain / part).is_file(), f"api/domains/{domain}/{part}"


@pytest.mark.parametrize("domain", NAMES)
def test_domain_entity_lives_in_core_domain(domain: str) -> None:
    assert importlib.util.find_spec(f"core_domain.{domain}.entities"), (
        f"core_domain/{domain}/entities.py"
    )


@pytest.mark.parametrize("domain", NAMES)
def test_domain_service_extends_the_service_base(domain: str) -> None:
    module = importlib.import_module(f"api.domains.{domain}.service")
    services = [
        cls
        for _, cls in inspect.getmembers(module, inspect.isclass)
        if cls.__module__ == module.__name__
    ]
    assert services, f"api/domains/{domain}/service.py defines no service"
    for cls in services:
        assert issubclass(cls, Service), f"{cls.__name__} must extend core_domain.ddd.Service"


def _repository_calls(method: ast.AST) -> set[str]:
    return {
        node.func.attr
        for node in ast.walk(method)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Attribute)
        and node.func.value.attr == "_repository"
    }


@pytest.mark.parametrize("domain", NAMES)
def test_domain_service_changes_entities_through_change(domain: str) -> None:
    """A method that loads and saves by hand skips the rule-then-save guarantee of change()."""
    tree = ast.parse((DOMAINS / domain / "service.py").read_text())
    by_hand = [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        and {"get", "save"} <= _repository_calls(node)
    ]
    assert not by_hand, f"api/domains/{domain}/service.py: use change_async in {by_hand}"
