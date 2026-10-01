# Build from the repo root, which the server's path dependencies need. compose.yaml does this;
# see the server README for how to run it. api/gen is copied from the host rather than generated
# here, so run server codegen before building.

ARG PYTHON_VERSION=3.13
ARG UV_VERSION=0.12.11

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

FROM python:${PYTHON_VERSION}-slim AS base
COPY --from=uv /uv /uvx /bin/
ENV UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never
WORKDIR /repo

# Dependencies are installed before the source is copied, so editing code does not invalidate
# this layer.
FROM base AS deps
COPY packages/proto/utils packages/proto/utils
COPY packages/organization-info packages/organization-info
COPY apps/server/pyproject.toml apps/server/uv.lock apps/server/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --project apps/server

FROM deps AS dev
# `uv run` would otherwise sync the venv again, adding the dev dependencies left out above, and at
# container start that needs network access.
ENV UV_NO_SYNC=1
COPY apps/server apps/server
WORKDIR /repo/apps/server
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "api"]
