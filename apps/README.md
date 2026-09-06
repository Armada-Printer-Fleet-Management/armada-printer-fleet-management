# `apps/` — the delivered applications

Each application wires concrete adapters from `plugins/` to the ports in
`packages/plugin-api/`, and exposes them as a running process.

| Directory | What it is |
|---|---|
| `server/` | Python ASGI service, ConnectRPC |
| `web/` | React + TypeScript browser app |
| `desktop/` | pywebview shell around a React frontend |

**Only code here may construct a concrete adapter.** Everything else depends on the port, never
the implementation.

The web and desktop apps are separate applications. They talk through the server and share code
only via `packages/`, never by importing each other.
