import pytest
from core_domain.ddd import AlreadyExists
from fastapi import HTTPException, status

from api.routers.domain_errors import domain_errors_as_http


def test_a_duplicate_is_a_conflict() -> None:
    with pytest.raises(HTTPException) as raised, domain_errors_as_http():
        raise AlreadyExists("user", "email")

    assert raised.value.status_code == status.HTTP_409_CONFLICT
