from fastapi import FastAPI
from starlette.routing import Mount

from api.common.consts import API_PREFIX


# The contract defines services the server does not implement yet; only mounted ones are served.
def mounted_services(app: FastAPI) -> set[str]:
    return {
        route.path.removeprefix(API_PREFIX + "/")
        for route in app.routes
        if isinstance(route, Mount) and route.path.startswith(API_PREFIX + "/")
    }
