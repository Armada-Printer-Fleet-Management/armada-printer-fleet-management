# The development image, run by infra/dev/compose.yaml with live reload; deploy.Dockerfile
# is the one that ships. Build from the repo root, which the server's path dependencies need.
# api/gen is copied from the host rather than generated here, so run server codegen first.

ARG PYTHON_VERSION=3.13
ARG UV_VERSION=0.12.11

# The official uv image, used only as a source to copy the uv program from.
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

# Python plus uv, the starting point of every later stage. The variables make uv copy packages
# rather than link them to its cache, and use this image's Python instead of downloading another.
FROM python:${PYTHON_VERSION}-slim AS base
COPY --from=uv /uv /uvx /bin/
ENV UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never
# Every later stage works in /repo, laid out like the repository so the relative paths between
# apps/ and packages/ still resolve.
WORKDIR /repo

# Installs the server's runtime dependencies, including the proto-utils and organization-info
# packages. Only the dependency files are copied, so editing server code leaves this stage cached.
FROM base AS deps
COPY packages/proto/utils packages/proto/utils
COPY packages/organization-info packages/organization-info
COPY apps/server/pyproject.toml apps/server/uv.lock apps/server/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --project apps/server

# The development image: the server's source, run by uvicorn and reloaded when compose syncs in
# an edit.
FROM deps AS dev
# `uv run` would otherwise sync the venv again, adding the dev dependencies left out above, and at
# container start that needs network access.
ENV UV_NO_SYNC=1
COPY apps/server apps/server
WORKDIR /repo/apps/server
EXPOSE 8000
# The same check as deploy.Dockerfile, run more often so the stack reports ready sooner. The slim
# image has no curl.
HEALTHCHECK --interval=5s --timeout=3s --retries=10 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health_check')"]
CMD ["uv", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "api"]
