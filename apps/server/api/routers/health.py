from fastapi import APIRouter

from api.common.models import HealthResponse
from api.services.application_info import ApplicationInfo


def health_router(application_info: ApplicationInfo) -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    async def health() -> HealthResponse:
        version_json = application_info.version()
        version = f"{version_json['major']}.{version_json['minor']}.{version_json['maintenance']}"
        if postfix := version_json.get("postfix"):
            version += f"-{postfix}"
        return HealthResponse(status="ok", version=version)

    return router
