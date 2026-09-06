# `apps/server/` — the backend service

Python, ASGI, ConnectRPC. Serves the contract in `packages/proto/` to both the web and desktop
applications.

**Belongs here:** the ASGI entry point, service implementations of the generated ConnectRPC
interfaces, the wiring that chooses which adapters to construct, and server configuration
loading.

**Does not belong here:** domain rules, which are `packages/core-domain/`, or adapter
implementations, which are `plugins/`.
