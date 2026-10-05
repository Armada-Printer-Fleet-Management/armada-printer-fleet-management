# The image that ships to deployed machines: Caddy serving the built frontend and forwarding /api
# to the server, one edge component rather than two. dev.Dockerfile is the local development one.
# Build from the repo root, which the shared packages and the .proto contract need. src/gen is
# generated inside the build, never copied from the host.

ARG NODE_VERSION=22
ARG CADDY_VERSION=2.11

# Node plus pnpm, the starting point of the build stages. Corepack runs the pnpm version that
# package.json names, so no separate pnpm install is needed.
FROM node:${NODE_VERSION}-slim AS base
RUN corepack enable
# Every later stage works in /repo, laid out like the repository so the relative paths between
# apps/ and packages/ still resolve.
WORKDIR /repo

# Installs the web app's dependencies, including the protoc-gen-es generator. Only the dependency
# files are copied, so editing web code leaves this stage cached. The web app is one member of the
# root pnpm workspace, so the install needs the workspace files and the manifest of every
# workspace package the app depends on.
FROM base AS deps
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY apps/web/package.json apps/web/
COPY packages/ui-kit/package.json packages/ui-kit/
COPY packages/organization-info/package.json packages/organization-info/
# The exact versions in pnpm-lock.yaml, for the web app and the workspace packages it depends on
# only; fails rather than updating the lock file if a package.json disagrees.
RUN pnpm install --frozen-lockfile --filter apps-web...

# Generates the web app's code from the .proto files, then builds the static site. The codegen
# tools exist only in this stage. buf is pinned with the SHA-256 it publishes, and must be bumped
# together with server/deploy.Dockerfile and the version /onboarding installs.
FROM deps AS build
ARG BUF_VERSION=1.72.0
ARG BUF_SHA256=8720830e26a733da55bb89bcd3cb44849c0965fc0c44fb5d691cccdc64dca5af
# curl and its certificates download buf; python3 runs scripts/generate_proto.py.
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl python3 \
 && rm -rf /var/lib/apt/lists/*
RUN set -eu; cd /tmp \
 && curl -fsSL -o buf "https://github.com/bufbuild/buf/releases/download/v${BUF_VERSION}/buf-Linux-x86_64" \
 && echo "${BUF_SHA256}  buf" | sha256sum -c - \
 && install -m 0755 buf /usr/local/bin/buf \
 && rm -f buf
COPY buf.yaml buf.gen.web_ts.yaml tsconfig.base.json ./
COPY packages/proto packages/proto
COPY packages/organization-info packages/organization-info
COPY packages/ui-kit packages/ui-kit
COPY scripts/generate_proto.py scripts/
COPY apps/web apps/web
# Writes apps/web/src/gen from packages/proto using the web's buf template, with node_modules/.bin
# on PATH so buf finds protoc-gen-es. Then vite build writes the static site to apps/web/dist.
RUN python3 scripts/generate_proto.py buf.gen.web_ts.yaml --node-modules apps/web/node_modules \
 && cd apps/web && pnpm build

# The image that ships. Built on Caddy rather than build, so Node, the dependencies, the codegen
# tools and the source stay behind; only the built files are copied across. Caddy's own start
# command reads /etc/caddy/Caddyfile, so replacing that file is all the setup it needs.
FROM caddy:${CADDY_VERSION}-alpine AS runtime
COPY infra/deploy/Caddyfile /etc/caddy/Caddyfile
# /srv is where the Caddyfile serves files from.
COPY --from=build /repo/apps/web/dist /srv
# Declared in the image so deployment tooling can tell whether an update came up healthy. Caddy's
# admin endpoint answers on loopback whatever the site address is.
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
    CMD ["wget", "-q", "-O", "/dev/null", "http://127.0.0.1:2019/config/"]
