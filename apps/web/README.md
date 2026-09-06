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
