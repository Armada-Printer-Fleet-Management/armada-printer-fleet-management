# `apps/server/` — the backend service

Python, ASGI, ConnectRPC. Serves the contract in `packages/proto/` to both the web and desktop
applications.

**Belongs here:** the ASGI entry point, service implementations of the generated ConnectRPC
interfaces, the wiring that chooses which adapters to construct, and server configuration
loading.

**Does not belong here:** domain rules, which are `packages/core-domain/`, or adapter
implementations, which are `plugins/`.

# Folder structure

```
apps/server/
├── api/
│   ├── common/      # contains any shared files that are fully internal to the api server (ex. consts and internal models)
│   ├── routers/     # ASGI routes for endpoints that don't fit the ConnectRPC model*
│   ├── services/    # Implementations of the generated ConnectRPC service interfaces
│   └── main.py      # ASGI entry point
├── tests/
│   ├── unit/
│   └── integration/
└── e2e/             # End-to-end tests; see e2e/README.md for required setup
```

*Ideally every endpoint should be implemented using the connectRPC protocol, however there may be cases where this is not possible.  In this case, you can make a regular REST api routing endpoint in the routers folder.