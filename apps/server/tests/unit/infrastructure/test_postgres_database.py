import asyncio
from collections.abc import Coroutine

import pytest
from core_domain.ddd import Unavailable
from sqlalchemy.ext.asyncio import create_async_engine

from api.infrastructure.postgres_database import PostgresDatabase

# Port 1 is reserved and never listening, so connecting is refused straight away.
_UNREACHABLE_URL = "postgresql+psycopg://armada:secret@127.0.0.1:1/armada"


def _run[T](coroutine: Coroutine[object, object, T]) -> T:
    # Async psycopg cannot run on Windows' default ProactorEventLoop.
    return asyncio.run(coroutine, loop_factory=asyncio.SelectorEventLoop)


def _unreachable() -> PostgresDatabase:
    return PostgresDatabase(lambda: create_async_engine(_UNREACHABLE_URL))


def test_engine_is_unavailable_before_opening() -> None:
    with pytest.raises(Unavailable):
        _unreachable().engine()


def test_health_check_is_unavailable_before_opening() -> None:
    with pytest.raises(Unavailable):
        _run(_unreachable().health_check())


def test_opening_does_not_connect() -> None:
    async def open_and_close() -> None:
        async with _unreachable() as database:
            database.engine()

    _run(open_and_close())


def test_health_check_is_unavailable_when_unreachable() -> None:
    async def check() -> None:
        async with _unreachable() as database:
            await database.health_check()

    with pytest.raises(Unavailable):
        _run(check())


def test_engine_is_unavailable_after_closing() -> None:
    async def open_and_close() -> PostgresDatabase:
        async with _unreachable() as database:
            return database

    database = _run(open_and_close())

    with pytest.raises(Unavailable):
        database.engine()
