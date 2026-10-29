"""Helpers for tests that run against a real Postgres. The fixtures themselves are in
tests/conftest.py."""

import asyncio
import os
from collections.abc import Coroutine

import pytest

needs_postgres = pytest.mark.skipif("DB_HOST" not in os.environ, reason="needs Postgres (DB_*)")


def run[T](coroutine: Coroutine[object, object, T]) -> T:
    # Async psycopg cannot run on Windows' default ProactorEventLoop.
    return asyncio.run(coroutine, loop_factory=asyncio.SelectorEventLoop)
