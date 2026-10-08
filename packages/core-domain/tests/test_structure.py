"""Every domain in core-domain has the same shape, and every entity keeps identity equality."""

import importlib
import inspect
from pathlib import Path

from core_domain.ddd import Entity

PACKAGE = Path(__file__).resolve().parents[1] / "src" / "core_domain"
NOT_DOMAINS = {"ddd", "ids", "__pycache__"}


def domains() -> list[str]:
    return sorted(p.name for p in PACKAGE.iterdir() if p.is_dir() and p.name not in NOT_DOMAINS)


def test_every_domain_has_an_entities_module() -> None:
    for domain in domains():
        assert (PACKAGE / domain / "entities.py").is_file(), f"core_domain/{domain}/entities.py"


def test_every_entity_keeps_identity_equality() -> None:
    for domain in domains():
        module = importlib.import_module(f"core_domain.{domain}.entities")
        for name, cls in inspect.getmembers(module, inspect.isclass):
            overrides = {"__eq__", "__hash__"} & set(vars(cls))
            if issubclass(cls, Entity) and cls is not Entity:
                assert not overrides, f"{domain}.{name} must be declared with @dataclass(eq=False)"
