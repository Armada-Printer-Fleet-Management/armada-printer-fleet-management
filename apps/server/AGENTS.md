# Agent Instructions: `apps/server/`

Path-scoped instructions for the application server. The root `AGENTS.md` still applies in full;
this file adds only what is specific to the server. Running it is in `README.md` beside this file.

The server is authoritative: it owns every entity's state, and its domains follow the root
`AGENTS.md` DDD section.

## Layout

| Path                   | Owns                                                                      |
| ---------------------- | ------------------------------------------------------------------------- |
| `api/main.py`          | Composition root: builds infrastructure, hands it to domain services, mounts RPC handlers |
| `api/domains/`         | Domains: a repository port and a service per domain. Every port extends a `core_domain.ddd` `Abstract*Repository` base, and its adapter inherits it; a port over state another service owns, such as printers, requests changes rather than saving |
| `api/infrastructure/`  | The server's own persistence behind those ports, and the adapters over plugins. A domain's SQL repository (`<domain>_sql.py`, on `SqlRepository`) is what the server runs; its in-memory one (`<domain>_memory.py`) serves tests, or the server until that domain has a SQL repository |
| `api/infrastructure/postgres_database.py` | The connection pool to Postgres, opened by the lifespan and probed by the health check |
| `api/infrastructure/sql_repository.py` | Base for a domain's SQL repository adapter: a transaction, with database failures as `Unavailable` |
| `api/infrastructure/enum_ids.py` | The UUID the database stores for each enum member. Never change or reuse one |
| `api/infrastructure/dev_data.py` | The one set of development data: the in-memory repositories start with it, tests use its IDs, `dev_seed.py` writes it |
| `migrations/`          | Alembic migrations. Foreign keys only inside a domain; enum columns are `uuid` from `enum_ids.py` |
| `dev_seed.py`          | Writes `dev_data.py` into the development database, run by the dev stack's `migrate` service. Never run by a deployment |
| `tests/contract/`      | What every repository adapter must do. A new adapter joins by adding its factory to `ADAPTERS` |
| `api/plugins.py`       | Builds the plugins each deployment chose in config, such as `FILE_STORE_BACKEND` |
| `api/services/`        | Connect handlers: translate between the wire and domain services, composing several where an RPC spans domains. No rules. `PrinterPoller` is the same kind of composer, run by the lifespan instead of a request |
| `api/routers/`         | REST routes that do not fit Connect, such as the health check and file bytes. Built from services handed in by `api/main.py`; domain errors go through `domain_errors_as_http()` |
| `api/gen/openapi/`     | Generated API documentation data. Gitignored                              |

## Adding a use case

Follow `print_job`, the worked example:

1. The rule goes on the entity in `packages/core-domain/core_domain/<domain>/entities.py`.
2. The use case goes on the domain service in `api/domains/<domain>/service.py`, using `change()`
   when it changes an entity. A rule that needs another domain's fact takes it as a plain value
   or a callback typed by ID, as `PrintJobService.submit` does, never that domain's types.
3. The handler in `api/services/` reads typed IDs with `request_id()`, calls the service inside
   `domain_errors_as_connect()`, and maps the result with the entity's mapper. Where an RPC spans
   domains, the handler calls each domain's service and joins the results, but holds no rules:
   `PrintJobServiceImplementation` passes `FileService.is_uploaded` into `submit` and returns a
   job beside its file.

## Using a plugin

A plugin reaches a domain only through infrastructure: domain service → the domain's port →
an adapter in `api/infrastructure/` → the plugin. `api/main.py` builds the plugin with
`api/plugins.py` and hands it to the adapter, which implements the domain's port in typed IDs
and domain terms, owns the plugin's lifetime and health check, and turns its errors into domain
errors: a missing item becomes `EntityNotFound` for the typed ID, an outage `Unavailable`.
`FileStoreFiles` is the example. Services, handlers, routes and `api/common/` never import a
plugin or its port, and import-linter enforces it. Never share an adapter through `app.state`.
