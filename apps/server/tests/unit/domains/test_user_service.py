import pytest
from core_domain.ddd import EntityNotFound
from core_domain.ids import UserId

from api.domains.auth.service import UserService
from api.infrastructure.dev_data import stub_users
from api.infrastructure.user_memory import InMemoryUserRepository
from tests.samples import NOW


@pytest.fixture
def service() -> UserService:
    return UserService(InMemoryUserRepository(stub_users()), clock=lambda: NOW)


async def test_user_reports_an_unknown_id(service: UserService) -> None:
    with pytest.raises(EntityNotFound):
        await service.user(UserId.new())
