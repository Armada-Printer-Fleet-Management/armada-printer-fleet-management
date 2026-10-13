from collections.abc import Mapping
from functools import cache
from typing import Annotated

from fastapi import Depends
from plugin_api.file_store import FileStore

from api.common.application_info import ApplicationInfo
from api.common.models import DependencyCheck
from api.common.settings import FileStoreSettings
from api.plugins import build_file_store


# Cached so pyproject.toml is read once, not on every request.
@cache
def application_info() -> ApplicationInfo:
    return ApplicationInfo()


# Cached so api/main.py, which opens it in the lifespan and hands it to services, and every
# Depends receive the same store.
@cache
def file_store() -> FileStore:
    return build_file_store(FileStoreSettings())


def file_store_check(store: FileStore) -> DependencyCheck:
    async def probe() -> bool:
        await store.health_check()
        return True

    return DependencyCheck(probe)


@cache
def dependency_checks() -> Mapping[str, DependencyCheck]:
    return {"file_storage": file_store_check(file_store())}


ApplicationInfoDep = Annotated[ApplicationInfo, Depends(application_info)]
DependencyChecksDep = Annotated[Mapping[str, DependencyCheck], Depends(dependency_checks)]
