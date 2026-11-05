import asyncio
from collections.abc import Iterator
from pathlib import Path

import boto3
import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from botocore.client import BaseClient
from botocore.config import Config as S3Config
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from api.common.settings import database_url
from api.infrastructure.postgres_database import PostgresDatabase
from api.main import app
from dev_seed import seed
from tests.integration.docker_stack import DockerStack
from tests.postgres import run, truncate_tables

ALEMBIC_INI = Path(__file__).parents[2] / "alembic.ini"


# Autouse, because every integration test needs Docker, and this makes the suite fail rather than
# quietly pass without it.
@pytest.fixture(scope="session", autouse=True)
def stack_environment() -> Iterator[dict[str, str]]:
    """Starts the dependencies once for the whole suite, migrated to head, and stops them after.
    Yields the environment variables the server reads to use them."""
    stack = DockerStack()
    try:
        environment = stack.start()
        # The migrations read DB_*, so they are set only while the migrations run.
        with pytest.MonkeyPatch.context() as monkeypatch:
            for name, value in environment.items():
                monkeypatch.setenv(name, value)
            command.upgrade(Config(ALEMBIC_INI), "head")
        yield environment
    finally:
        stack.stop()


@pytest.fixture(scope="session")
def file_store_client(stack_environment: dict[str, str]) -> BaseClient:
    return boto3.client(
        "s3",
        endpoint_url=stack_environment["FILE_STORE_ENDPOINT_URL"],
        region_name=stack_environment["FILE_STORE_REGION"],
        aws_access_key_id=stack_environment["FILE_STORE_ACCESS_KEY"],
        aws_secret_access_key=stack_environment["FILE_STORE_SECRET_KEY"],
        config=S3Config(s3={"addressing_style": "path"}),
    )


def _reset_database() -> None:
    engine = sa.create_engine(database_url())
    try:
        truncate_tables(engine)
        seed(engine)
    finally:
        engine.dispose()


def _empty_bucket(client: BaseClient, bucket: str) -> None:
    for page in client.get_paginator("list_objects_v2").paginate(Bucket=bucket):
        for stored in page.get("Contents", []):
            client.delete_object(Bucket=bucket, Key=stored["Key"])


# Autouse, because no test may see what another left behind. Setting the environment per test also
# keeps DB_* and the rest from reaching the unit tests in the same run.
@pytest.fixture(autouse=True)
def reset_dependencies(
    stack_environment: dict[str, str],
    file_store_client: BaseClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Points the server's settings at the stack, then restores the seeded data and an empty
    bucket, keeping the migrations in place."""
    for name, value in stack_environment.items():
        monkeypatch.setenv(name, value)
    _reset_database()
    _empty_bucket(file_store_client, stack_environment["FILE_STORE_BUCKET"])


@pytest.fixture
def postgres_database() -> Iterator[PostgresDatabase]:
    """An open PostgresDatabase over the stack's database."""
    # NullPool, because each run() is a new event loop and a pooled connection belongs to the
    # loop that opened it.
    database = PostgresDatabase(lambda: create_async_engine(database_url(), poolclass=NullPool))
    run(database.__aenter__())
    try:
        yield database
    finally:
        run(database.__aexit__(None, None, None))


@pytest.fixture
def app_client(restore_logging: None) -> Iterator[TestClient]:
    """The real application with its lifespan running against the stack."""
    # Async psycopg cannot run on Windows' default ProactorEventLoop.
    with TestClient(app, backend_options={"loop_factory": asyncio.SelectorEventLoop}) as client:
        yield client
