from fastapi import FastAPI
from organization_info import read

from api.gen.common.v1 import organization_info_pb2
from api.routers.health import health_router
from api.services.application_info import ApplicationInfo

app = FastAPI(title=read(organization_info_pb2.OrganizationInfo()).title)
app.include_router(health_router(ApplicationInfo()))
