from typing import cast

import pytest
from core_domain.ddd import Unavailable
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine

from api.infrastructure.postgres_database import PostgresDatabase

# Port 1 is reserved and never listening, so connecting is refused straight away.
_UNREACHABLE_URL = "postgresql+psycopg://armada:secret@127.0.0.1:1/armada"


def _unreachable() -> PostgresDatabase:
    return PostgresDatabase(lambda: create_async_engine(_UNREACHABLE_URL))


def test_engine_is_unavailable_before_opening() -> None:
    with pytest.raises(Unavailable):
        _unreachable().engine()


async def test_health_check_is_unavailable_before_opening() -> None:
    with pytest.raises(Unavailable):
        await _unreachable().health_check()


async def test_opening_does_not_connect() -> None:
    async with _unreachable() as database:
        database.engine()


class _RefusedConnection:
    async def __aenter__(self) -> AsyncConnection:
        raise OperationalError("SELECT 1", {}, OSError("connection refused"))

    async def __aexit__(self, *exc_info: object) -> None:
        return None


class _RefusingEngine:
    """An engine whose every connection is refused, as the driver reports it."""

    def connect(self) -> _RefusedConnection:
        return _RefusedConnection()

    async def dispose(self) -> None:
        return None


async def test_health_check_is_unavailable_when_unreachable() -> None:
    # Only connect and dispose are used, which the stub provides.
    database = PostgresDatabase(lambda: cast(AsyncEngine, _RefusingEngine()))

    async with database:
        with pytest.raises(Unavailable):
            await database.health_check()


async def test_engine_is_unavailable_after_closing() -> None:
    async with _unreachable() as database:
        pass

    with pytest.raises(Unavailable):
        database.engine()
