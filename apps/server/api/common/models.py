from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["pass", "fail"]
    version: str | None = None
    dependencies: dict[str, str] | None = None
