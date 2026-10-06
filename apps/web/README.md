# `apps/web/` — the browser application

Student-facing web application for submitting print jobs. Communicates with the remote server only. The server then handles the requests.
Additionally, has a admin settings for site specific configurations.

React, TypeScript and Vite. Talks to `apps/server/` over ConnectRPC through the client in
`packages/api-client/`.

**Belongs here:** routes, pages, application state, and composition of components from
`packages/ui-kit/`.

**Does not belong here:** reusable presentational components (`packages/ui-kit/`), API call
plumbing (`packages/api-client/`), or anything imported by `apps/desktop/`. The two frontends
are separate applications and share code only through `packages/`.

## Run in Docker

The web app runs in the development stack in `infra/dev/`, alongside the server, Postgres and
Garage. The dev image uses the `src/gen` already generated on the host, so generate it first (step
1 below), then from the repo root:

```
python scripts/compose_run.py dev
```

This serves `http://127.0.0.1:5174` and reloads on changes under `src/`. Requests to `/api` are
forwarded to the server container, as Caddy does in deployment.

| File | Image |
|---|---|
| `dev.Dockerfile` | Development: the Vite dev server, with `src/gen` copied from the host |
| `deploy.Dockerfile` | What ships: Caddy serving the built app and forwarding `/api` to the server, using `infra/deploy/Caddyfile`. Generates its own `src/gen` with a pinned, checksum-verified `buf` |

Both build from the repo root, each with its own allow-list, `<name>.Dockerfile.dockerignore`, and
install only the web app's part of the root pnpm workspace (`pnpm install --filter apps-web...`).
When the app gains a dependency on another package from `packages/`, allow that package in both
allow-lists and copy its `package.json` in both Dockerfiles' `deps` stage.

## Run locally

Prerequisites:
- Node.js (16+ recommended) and pnpm installed globally. See https://pnpm.io/installation

Commands:
1. Install dependencies from the repository root

   pnpm install

   Then, from the repo root, generate the protobuf code the app imports (gitignored):

   python scripts/generate_proto.py buf.gen.web_ts.yaml --node-modules apps/web/node_modules

2. Start the development server (Vite)

   pnpm --filter apps-web dev

   The dev server serves the app at http://localhost:5174, forwarding `/api` to the server at
   http://127.0.0.1:8000 (override with `API_PROXY_TARGET`).

3. Build for production

   pnpm --filter apps-web build

4. Preview the production build locally

   pnpm --filter apps-web preview

Notes:
- The web frontend talks to the backend in `apps/server/` via `packages/api-client/`. Start the
  server before using features that require the API, and ensure it is reachable from the browser.
- If the backend is running on a different host or port, update the appropriate client configuration
  or environment values so the frontend can reach the server.

Folder structure (apps/web)
- src/
  - components/     # Presentational and composed app components (feature-stable)
  - features/       # Feature folders: pages, state, and feature-specific components
  - lib/            # Small utilities
  - routes/         # Route definitions and route-level loaders
  - styles/         # Global styles, Tailwind directives, design tokens
  - tests/          # Unit and integration tests (Vitest + React Testing Library)