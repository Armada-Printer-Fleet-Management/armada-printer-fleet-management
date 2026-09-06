# `apps/desktop/frontend/` — the desktop UI

The React application rendered inside the pywebview window, built to static assets that
`../shell/` serves.

Shares components with `apps/web/` through `packages/ui-kit/`, never by importing the web app
directly.
