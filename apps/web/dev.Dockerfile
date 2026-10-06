# The development image, run by infra/dev/compose.yaml with live reload; deploy.Dockerfile is
# the one that ships. Build from the repo root, which the shared packages need. src/gen is copied
# from the host rather than generated here, so run web codegen first.

ARG NODE_VERSION=22

# Node plus pnpm, the starting point of every later stage. Corepack runs the pnpm version that
# package.json names, so no separate pnpm install is needed.
FROM node:${NODE_VERSION}-slim AS base
RUN corepack enable
# Every later stage works in /repo, laid out like the repository so the relative paths between
# apps/ and packages/ still resolve.
WORKDIR /repo

# Installs the web app's dependencies. Only the dependency files are copied, so editing web code
# leaves this stage cached. The web app is one member of the root pnpm workspace, so the install
# needs the workspace files and the manifest of every workspace package the app depends on.
FROM base AS deps
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY apps/web/package.json apps/web/
COPY packages/ui-kit/package.json packages/ui-kit/
COPY packages/organization-info/package.json packages/organization-info/
# Only the web app and the workspace packages it depends on, not the desktop frontend.
RUN pnpm install --frozen-lockfile --filter apps-web...

# The development image: Vite's dev server, reloading when compose syncs in an edit.
FROM deps AS dev
COPY tsconfig.base.json ./
COPY packages/organization-info packages/organization-info
COPY packages/ui-kit packages/ui-kit
COPY apps/web apps/web
WORKDIR /repo/apps/web
EXPOSE 5174
# Asks the Vite dev server for the page, where deploy.Dockerfile asks Caddy. The slim image has no
# curl or wget.
HEALTHCHECK --interval=5s --timeout=3s --retries=10 \
    CMD ["node", "-e", "fetch('http://127.0.0.1:5174/').then((r) => process.exit(r.ok ? 0 : 1), () => process.exit(1))"]
CMD ["pnpm", "dev", "--host", "0.0.0.0"]
