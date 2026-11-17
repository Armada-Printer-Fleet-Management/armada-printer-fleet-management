import pytest
from fastapi.testclient import TestClient

from tests.fake_app import FakeApp, fake_services
from tests.fakes import MemoryFileStore


@pytest.fixture
def client(fake_app: FakeApp) -> TestClient:
    """The real app over the default fakes. A test needing other fakes calls fake_app itself."""
    return fake_app()


@pytest.fixture
def store() -> MemoryFileStore:
    """An empty file store, for a test that inspects or breaks the bytes it holds."""
    return MemoryFileStore()


@pytest.fixture
def file_client(fake_app: FakeApp, store: MemoryFileStore) -> TestClient:
    """The app over the default fakes, storing bytes in store so a test can inspect or break it."""
    return fake_app(fake_services(store=store))
