from collections.abc import Mapping
from functools import cache
from typing import Annotated

from fastapi import Depends

from api.common.application_information import ApplicationInformation
from api.common.dependency_checks import DependencyCheck


# Cached so pyproject.toml is read once, not on every request.
@cache
def application_information() -> ApplicationInformation:
    return ApplicationInformation()


# Stub: stands in for real dependency checks until the server has dependencies. Filling it in
# means replacing each entry in dependency_checks() with an async function that probes it.
async def _placeholder_dependency_check() -> bool:
    return True


@cache
def dependency_checks() -> Mapping[str, DependencyCheck]:
    return {
        "database": _placeholder_dependency_check,
        "external_service": _placeholder_dependency_check,
    }


ApplicationInformationDep = Annotated[ApplicationInformation, Depends(application_information)]
DependencyChecksDep = Annotated[Mapping[str, DependencyCheck], Depends(dependency_checks)]
