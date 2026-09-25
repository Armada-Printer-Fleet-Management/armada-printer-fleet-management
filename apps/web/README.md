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

## Run locally

Prerequisites:
- Node.js (16+ recommended) and pnpm installed globally. See https://pnpm.io/installation

Commands:
1. Install dependencies

   cd apps/web
   pnpm install

   Then, from the repo root, generate the protobuf code the app imports (gitignored):

   python scripts/generate_proto.py buf.gen.web_ts.yaml --node-modules apps/web/node_modules

2. Start the development server (Vite)

   pnpm run dev

   The dev server serves the app at http://localhost:5173 by default.

3. Build for production

   pnpm run build

4. Preview the production build locally

   pnpm run preview

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