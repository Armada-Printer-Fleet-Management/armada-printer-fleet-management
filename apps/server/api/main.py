from fastapi import FastAPI

from api.routers.health import health_router
from api.services.application_information import ApplicationInformation

app = FastAPI(title="Fleet management server")
app.include_router(health_router(ApplicationInformation()))
