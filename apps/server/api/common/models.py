from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum

from pydantic import BaseModel


class HealthStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    DEGRADED = "degraded"


@dataclass(frozen=True)
class DependencyCheck:
    probe: Callable[[], Awaitable[bool]]
    critical: bool = True


class HealthReport(BaseModel):
    status: HealthStatus
    version: str | None
    dependencies: dict[str, str] | None


class HealthResponse(BaseModel):
    status: HealthStatus
    version: str | None = None
    dependencies: dict[str, str] | None = None
