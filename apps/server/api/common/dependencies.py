from functools import cache
from typing import Annotated

from fastapi import Depends

from api.common.application_info import ApplicationInfo


# Cached so pyproject.toml is read once, not on every request.
@cache
def application_info() -> ApplicationInfo:
    return ApplicationInfo()


ApplicationInfoDep = Annotated[ApplicationInfo, Depends(application_info)]
