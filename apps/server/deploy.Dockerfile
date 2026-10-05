# The image that ships to deployed machines; dev.Dockerfile is the local development one. Build
# from the repo root, which the server's path dependencies and the .proto contract need.
# api/gen is generated inside the build, never copied from the host, so a stale local copy
# cannot ship.

ARG PYTHON_VERSION=3.13
ARG UV_VERSION=0.12.11

# The official uv image, used only as a source to copy the uv program from.
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

# Python plus uv, the starting point of every later stage, including the image that ships. The
# variables make uv copy packages rather than link them to its cache, use this image's Python
# instead of downloading another, and precompile packages so the server starts faster.
FROM python:${PYTHON_VERSION}-slim AS base
COPY --from=uv /uv /uvx /bin/
ENV UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_COMPILE_BYTECODE=1

# Every later stage works in /repo, laid out like the repository so the relative paths between
# apps/ and packages/ still resolve.
WORKDIR /repo

# Installs the server's dependencies, including the proto-utils and organization-info packages.
# Only the dependency files are copied, so editing server code leaves this stage cached.
FROM base AS deps
COPY packages/proto/utils packages/proto/utils
COPY packages/organization-info packages/organization-info
COPY apps/server/pyproject.toml apps/server/uv.lock apps/server/
# Runtime packages only (--no-dev). The image that ships inherits this virtualenv.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --project apps/server

# Generates the server's code from the .proto files. The codegen tools exist only in this stage.
# Each is pinned with the SHA-256 its publisher lists, and must be bumped together with the
# versions /onboarding installs on developer machines.
FROM deps AS codegen
ARG BUF_VERSION=1.72.0
ARG BUF_SHA256=8720830e26a733da55bb89bcd3cb44849c0965fc0c44fb5d691cccdc64dca5af
ARG PROTOC_VERSION=36.0
ARG PROTOC_SHA256=bc8211ce760bd43ee21ddc145d6d9dbaeeabae205267a79d9054a240e367d4b4
# The SPEC_PLUGIN pair pins protoc-gen-connect-openapi, which writes the OpenAPI spec.
ARG SPEC_PLUGIN_VERSION=0.28.0
ARG SPEC_PLUGIN_SHA256=1bc500494b835efa00487d9685ca8e6f74b5a427bdb6f5a456f3287e5f3b336a
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl unzip \
 && rm -rf /var/lib/apt/lists/*
RUN set -eu; cd /tmp \
 && curl -fsSL -o buf "https://github.com/bufbuild/buf/releases/download/v${BUF_VERSION}/buf-Linux-x86_64" \
 && echo "${BUF_SHA256}  buf" | sha256sum -c - \
 && install -m 0755 buf /usr/local/bin/buf \
 && curl -fsSL -o protoc.zip "https://github.com/protocolbuffers/protobuf/releases/download/v${PROTOC_VERSION}/protoc-${PROTOC_VERSION}-linux-x86_64.zip" \
 && echo "${PROTOC_SHA256}  protoc.zip" | sha256sum -c - \
 && unzip -q protoc.zip -d /usr/local bin/protoc 'include/*' \
 && curl -fsSL -o openapi.tar.gz "https://github.com/sudorandom/protoc-gen-connect-openapi/releases/download/v${SPEC_PLUGIN_VERSION}/protoc-gen-connect-openapi_${SPEC_PLUGIN_VERSION}_linux_amd64.tar.gz" \
 && echo "${SPEC_PLUGIN_SHA256}  openapi.tar.gz" | sha256sum -c - \
 && tar -xzf openapi.tar.gz -C /usr/local/bin protoc-gen-connect-openapi \
 && rm -f /tmp/buf /tmp/protoc.zip /tmp/openapi.tar.gz

# Adds the dev dependencies, which include the protoc-gen-connectrpc generator, to this stage's
# virtualenv only. The runtime stage copies just apps/server/api from here, so neither they nor
# the codegen tools ship.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --project apps/server
COPY buf.yaml buf.gen.server.yaml ./
COPY packages/proto packages/proto
COPY scripts/generate_proto.py scripts/
COPY apps/server apps/server

# Writes apps/server/api/gen from packages/proto using the server's buf template. uv run puts
# the virtualenv's generator on PATH, where buf looks for it.
RUN uv run --locked --project apps/server python scripts/generate_proto.py buf.gen.server.yaml

# The image that ships. Built on deps rather than codegen, so the dev dependencies and codegen
# tools stay behind.
FROM deps AS runtime
RUN useradd --system --uid 10001 --no-create-home armada
USER armada
COPY --from=codegen /repo/apps/server/api apps/server/api
WORKDIR /repo/apps/server
ENV PATH="/repo/apps/server/.venv/bin:${PATH}" \
    UV_NO_SYNC=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
EXPOSE 8000
# Declared in the image, not only in compose: deployment tooling reads it to decide whether an
# update came up healthy. The slim image has no curl.
HEALTHCHECK --interval=15s --timeout=3s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health_check')"]
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
