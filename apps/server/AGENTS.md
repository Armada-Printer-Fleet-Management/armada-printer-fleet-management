# Agent Instructions: `apps/server/`

Path-scoped instructions for the application server. The root `AGENTS.md` still applies in full;
this file adds only what is specific to the server. Running it is in `README.md` beside this file.

The server is authoritative: it owns every entity's state, and its domains follow the root
`AGENTS.md` DDD section.

## Layout

| Path                   | Owns                                                                      |
| ---------------------- | ------------------------------------------------------------------------- |
| `api/main.py`          | Composition root: builds infrastructure, hands it to domain services, mounts RPC handlers |
| `api/domains/`         | Domains: a repository port and a service per domain                      |
| `api/infrastructure/`  | The server's own persistence behind those ports                           |
| `api/services/`        | Connect handlers: translate between the wire and a domain service, nothing else |
| `api/routers/`         | REST routes that do not fit Connect, such as the health check             |
| `api/gen/openapi/`     | Generated API documentation data. Gitignored                              |

## Adding a use case

Follow `print_job`, the worked example:

1. The rule goes on the entity in `packages/core-domain/core_domain/<domain>/entities.py`.
2. The use case goes on the domain service in `api/domains/<domain>/service.py`, using `change()`
   when it changes an entity.
3. The handler in `api/services/` reads typed IDs with `request_id()`, calls the service inside
   `domain_errors_as_connect()`, and maps the result with the entity's mapper.