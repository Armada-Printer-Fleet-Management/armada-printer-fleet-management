"""Every desktop domain has the same shape: a repository port and a service, over an entity that
lives once in core_domain, or in the domain itself when only the desktop uses it."""

import importlib
import importlib.util
import inspect
from pathlib import Path

import pytest
from core_domain.ddd import Service

import armada_domains

DOMAINS = Path(armada_domains.__file__).parent
NAMES = sorted(p.name for p in DOMAINS.iterdir() if p.is_dir() and any(p.glob("*.py")))


def test_domains_are_found() -> None:
    assert NAMES


@pytest.mark.parametrize("domain", NAMES)
def test_domain_has_a_repository_and_a_service(domain: str) -> None:
    for part in ("repository.py", "service.py"):
        assert (DOMAINS / domain / part).is_file(), f"armada_domains/{domain}/{part}"


@pytest.mark.parametrize("domain", NAMES)
def test_domain_entity_is_shared_or_desktop_only(domain: str) -> None:
    # A shared entity lives once in core_domain; one only the desktop uses lives in its domain.
    desktop_only = (DOMAINS / domain / "entities.py").is_file()
    assert desktop_only or importlib.util.find_spec(f"core_domain.{domain}.entities"), (
        f"core_domain/{domain}/entities.py or armada_domains/{domain}/entities.py"
    )


@pytest.mark.parametrize("domain", NAMES)
def test_domain_service_extends_the_service_base(domain: str) -> None:
    module = importlib.import_module(f"armada_domains.{domain}.service")
    services = [
        cls
        for _, cls in inspect.getmembers(module, inspect.isclass)
        if cls.__module__ == module.__name__
    ]
    assert services, f"armada_domains/{domain}/service.py defines no service"
    for cls in services:
        assert issubclass(cls, Service), f"{cls.__name__} must extend core_domain.ddd.Service"
