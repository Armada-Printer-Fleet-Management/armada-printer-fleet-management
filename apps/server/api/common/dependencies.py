from collections.abc import Mapping
from functools import cache
from typing import Annotated

from fastapi import Depends

from api.common.application_info import ApplicationInfo
from api.common.models import DependencyCheck


# Cached so pyproject.toml is read once, not on every request.
@cache
def application_info() -> ApplicationInfo:
    return ApplicationInfo()


# Stub: stands in for real dependency checks until the server has dependencies. Filling it in
# means replacing each entry in dependency_checks() with a DependencyCheck wrapping an async
# function that probes it, marked critical=False if the service can run without it.
async def _placeholder_dependency_check() -> bool:
    return True


def dependency_checks() -> Mapping[str, DependencyCheck]:
    return {
        "example_1": DependencyCheck(_placeholder_dependency_check),
        "example_2": DependencyCheck(_placeholder_dependency_check, critical=False),
    }


ApplicationInfoDep = Annotated[ApplicationInfo, Depends(application_info)]
DependencyChecksDep = Annotated[Mapping[str, DependencyCheck], Depends(dependency_checks)]
