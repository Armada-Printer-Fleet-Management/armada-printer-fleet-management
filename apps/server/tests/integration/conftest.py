import asyncio
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import boto3
import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from botocore.config import Config as S3Config
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine
from types_boto3_s3.client import S3Client

from api.app import build_app
from api.common.settings import database_url
from api.infrastructure.postgres_database import PostgresDatabase
from api.main import production_parts
from dev_seed import seed
from tests.integration.utils.docker_stack import DockerStack
from tests.integration.utils.file_store import empty_bucket
from tests.postgres import truncate_tables

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
def file_store_client(stack_environment: dict[str, str]) -> S3Client:
    # boto3.client is overloaded for every AWS service, and only the S3 stubs are installed, so
    # pyright sees the overload set itself as partly unknown; the S3 overload it picks is typed.
    return boto3.client(  # pyright: ignore[reportUnknownMemberType]
        "s3",
        endpoint_url=stack_environment["FILE_STORE_ENDPOINT_URL"],
        region_name=stack_environment["FILE_STORE_REGION"],
        aws_access_key_id=stack_environment["FILE_STORE_ACCESS_KEY"],
        aws_secret_access_key=stack_environment["FILE_STORE_SECRET_KEY"],
        config=S3Config(s3={"addressing_style": "path"}),
    )


@pytest.fixture(scope="session")
def database_engine(stack_environment: dict[str, str]) -> Iterator[sa.Engine]:
    """A synchronous engine on the stack's database, for setting up and checking its rows."""
    # database_url reads DB_*, which is set only while the URL is built.
    with pytest.MonkeyPatch.context() as monkeypatch:
        for name, value in stack_environment.items():
            monkeypatch.setenv(name, value)
        url = database_url()
    engine = sa.create_engine(url)
    yield engine
    engine.dispose()


# Autouse, because no test may see what another left behind. Setting the environment per test also
# keeps DB_* and the rest from reaching the unit tests in the same run.
@pytest.fixture(autouse=True)
def reset_dependencies(
    stack_environment: dict[str, str],
    file_store_client: S3Client,
    database_engine: sa.Engine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Points the server's settings at the stack, then restores the seeded data and an empty
    bucket, keeping the migrations in place."""
    for name, value in stack_environment.items():
        monkeypatch.setenv(name, value)
    truncate_tables(database_engine)
    seed(database_engine)
    empty_bucket(file_store_client, stack_environment["FILE_STORE_BUCKET"])


@pytest.fixture
async def postgres_database() -> AsyncIterator[PostgresDatabase]:
    """An open PostgresDatabase over the stack's database, on the test's own event loop."""
    async with PostgresDatabase(lambda: create_async_engine(database_url())) as database:
        yield database


@pytest.fixture
def app_client(restore_logging: None) -> Iterator[TestClient]:
    """The production-wired application with its lifespan running against the stack. It is built
    for each test, so no test sees the in-memory state another left behind."""
    app = build_app(production_parts())
    # Async psycopg cannot run on Windows' default ProactorEventLoop.
    with TestClient(app, backend_options={"loop_factory": asyncio.SelectorEventLoop}) as client:
        yield client
