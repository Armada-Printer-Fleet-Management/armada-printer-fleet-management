from connectrpc.server import ConnectASGIApplication
from fastapi import FastAPI
from starlette.types import Receive, Scope, Send

from api.common.consts import API_PREFIX


# connectrpc strips the whole mount path before matching procedures, so a plain app.mount under
# API_PREFIX 404s. Trimming the service's own path off root_path leaves only the prefix to strip.
def mount_rpc[S](app: FastAPI, service: ConnectASGIApplication[S]) -> None:
    async def prefixed(scope: Scope, receive: Receive, send: Send) -> None:
        root_path = str(scope["root_path"]).removesuffix(service.path)
        await service({**scope, "root_path": root_path}, receive, send)

    app.mount(API_PREFIX + service.path, prefixed)
