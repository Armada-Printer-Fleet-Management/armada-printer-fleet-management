# `apps/desktop/frontend/` — the desktop UI

The React application rendered inside the pywebview window, built to static assets that
`../backend/` serves.

Shares components with `apps/web/` through `packages/ui-kit/`, never by importing the web app
directly.

Install dependencies from the repository root with `pnpm install`. Run the desktop frontend
with `pnpm --filter desktop-frontend dev` and build it with `pnpm --filter desktop-frontend
build`.
