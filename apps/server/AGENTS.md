# Agent Instructions: `apps/server/`

Path-scoped instructions for the application server. The root `AGENTS.md` still applies in full;
this file adds only what is specific to the server. The commands a person types to run it are in
`README.md` beside this file.

The server is authoritative: it owns every entity's state, and its domains follow the root
`AGENTS.md` DDD section. Domain rules belong in `packages/core-domain/` and adapter
implementations in `plugins/`, never here.

## Layout

| Path                   | Owns                                                                      |
| ---------------------- | ------------------------------------------------------------------------- |
| `api/main.py`          | ASGI entry point and composition root: builds infrastructure, hands it to domain services, mounts RPC handlers |
| `api/domains/`         | Domains: a repository port and a service per domain. Every port extends a `core_domain.ddd` `Abstract*Repository` base, and its adapter inherits it; a port over state another service owns, such as printers, requests changes rather than saving |
| `api/infrastructure/`  | The server's own persistence behind those ports, and the adapters over plugins. A domain's SQL repository (`<domain>_sql.py`, on `SqlRepository`) is what the server runs; its in-memory one (`<domain>_memory.py`) serves tests, or the server until that domain has a SQL repository |
| `api/infrastructure/postgres_database.py` | The connection pool to Postgres, opened by the lifespan and probed by the health check |
| `api/infrastructure/sql_repository.py` | Base for a domain's SQL repository adapter: a transaction, with database failures as `Unavailable` |
| `api/infrastructure/enum_ids.py` | The UUID the database stores for each enum member. Never change or reuse one |
| `api/infrastructure/dev_data.py` | The one set of development data: the in-memory repositories start with it, tests use its IDs, `dev_seed.py` writes it |
| `migrations/`, `alembic.ini` | Alembic migrations. Foreign keys only inside a domain; enum columns are `uuid` from `enum_ids.py`. `alembic.ini` holds no connection details |
| `dev_seed.py`          | Writes `dev_data.py` into the development database, run by the dev stack's `migrate` service. Never run by a deployment |
| `tests/`, `e2e/`       | The server's tests. `tests/AGENTS.md` holds their layout and rules; `e2e/README.md` has the end-to-end setup |
| `api/plugins.py`       | Builds the plugins each deployment chose in config, such as `FILE_STORE_BACKEND` |
| `api/common/authentication.py` | `Role`, `Caller` and the current caller, which only `authenticated_as` sets. A caller's `subject` is the identity provider's ID, not a `UserId` |
| `api/common/access_policy.py` | `ACCESS`, the roles allowed on each endpoint. Every endpoint must be listed: an unlisted one allows no role. The most specific row wins, so one procedure can override its service |
| `api/middleware/authentication.py` | Verifies the bearer token (bad token: 401, no token: no caller), then checks `ACCESS`. A refusal is logged, and rejected with 401 or 403 only when `AUTH_ENFORCE` is set |
| `api/infrastructure/oidc_access_tokens.py` | Wraps the `TokenVerifier` plugin: its result becomes a `Caller`, a rejected token `InvalidAccessToken`, an outage `Unavailable` |
| `api/services/`        | Connect handlers: translate between the wire and domain services, composing several where an RPC spans domains. No rules. `PrinterPoller` is the same kind of composer, run by the lifespan instead of a request |
| `api/routers/`         | REST routes that do not fit Connect, such as the health check and file bytes. Built from services handed in by `api/main.py`; domain errors go through `domain_errors_as_http()`. Prefer Connect; REST only where Connect cannot work |
| `api/common/`          | Shared code internal to the server, such as constants, `health.py` and `openapi.py` |
| `api/middleware/`      | ASGI middleware wrapping every request, REST and Connect alike |
| `api/lifespan.py`      | Startup and shutdown: configures logging and opens the infrastructure |
| `api/logging_config.py` | structlog configuration |
| `api/gen/`             | Generated code, including `openapi/`. Gitignored                          |
| `dev.Dockerfile`, `deploy.Dockerfile` | The development image (generated code copied from the host) and the image that ships (generates its own code with pinned, checksum-verified tools; non-root, no dev dependencies, JSON logs) |
| `*.Dockerfile.dockerignore` | Each image's allow-list for its build context, the repo root. Docker uses it in place of the root `.dockerignore` |
| `dev_run.py`           | Runs `api.main:app` natively on `127.0.0.1:8000`, with `--dev` reloading on changes under `api/`. Stops with a pointer to `/onboarding` if `uv` or the generated code is missing |
| `export_openapi.py`    | Writes the API spec into `docs/api/` |

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

Picture: `docs/domain-architecture.html`.

## Using a plugin

A plugin reaches a domain only through infrastructure: domain service → the domain's port →
an adapter in `api/infrastructure/` → the plugin. `api/main.py` builds the plugin with
`api/plugins.py` and hands it to the adapter, which implements the domain's port in typed IDs
and domain terms, owns the plugin's lifetime and health check, and turns its errors into domain
errors: a missing item becomes `EntityNotFound` for the typed ID, an outage `Unavailable`.
`FileStoreFiles` is the example. Services, handlers, routes and `api/common/` never import a
plugin or its port, and import-linter enforces it.

## Routes

- **Every route, REST and Connect, is served under `/api`.** Connect clients use
  `http://<host>:8000/api` as their base URL. Mount a new RPC service with `mount_rpc` in
  `api/main.py`; a plain `app.mount` under the prefix returns 404. Connect services mount at their
  generated `path`, so all share one base URL.
- **File bytes are REST**, because Connect cannot stream them from a browser. A
  `Create<Thing>Upload` RPC creates the file record and returns its `upload_url`, an absolute URL
  on the origin the caller reached (the `Host` header, and `X-Forwarded-Proto` behind a proxy).
  - `PUT /api/files/{file_id}` stores the raw body. It must match the record's size and SHA-256,
    or it is refused with a 400 and nothing is stored.
  - `GET /api/files/{file_id}` streams the bytes back as an attachment named after the file.
  - `DELETE /api/files/{file_id}` deletes the record, and its bytes unless another file holds the
    same content. Bytes are stored once per content, under `<sha256>.<file type>`.
- **Health is exposed twice from one implementation**, `api/common/health.py`:
  `GET /api/health_check` (plain `pass`/`degraded`/`fail`; `?full=true` for JSON with the version,
  `?check_dependencies=true` to run dependency checks; only `fail` is a 503) and
  `POST /api/server.v1.HealthCheckService/HealthCheck` (same options in the request,
  `STATUS_PASS`/`STATUS_DEGRADED`/`STATUS_FAIL` in the response). A failing dependency fails the
  service unless its `DependencyCheck` is `critical=False`, which degrades it instead.
  `identity_provider` is one: requests without a token still work while it is down.
- **Never put shared objects on `app.state`.** It is untyped, so pyright cannot check reads, and
  tests cannot replace it through `app.dependency_overrides`. Give a REST route what it needs
  through `Depends` or its router factory, and a Connect handler or domain service through its
  constructor in `api/main.py`.

## Access tokens

- A request may carry `Authorization: Bearer <access token>` from the identity provider. The
  server checks the token's signature, issuer (`AUTH_ISSUER`), audience (`AUTH_AUDIENCE`) and
  expiry, and reads the caller's roles. A bad token is a 401; a request without one runs with no
  caller.
- It then checks the caller against `ACCESS` in `api/common/access_policy.py`, which lists the
  roles allowed on every endpoint. A refusal is logged as `access would be denied`. With
  `AUTH_ENFORCE=true` it is rejected instead: 401 without a token, 403 for a role not allowed.
- Every error body is Connect-shaped, `{"code": ..., "message": ...}`, for REST routes too.
- The issuer and the key address differ in the stacks on purpose: tokens name the public address,
  while the server fetches keys over the internal one. In the deploy stack the issuer defaults to
  `https://<DOMAIN>/auth/realms/armada`; set `AUTH_ISSUER` in `config/compose.deploy.env` when
  `DOMAIN` is `:80`.

## Database

- The dev stack's `migrate` service runs `alembic upgrade head` and then `dev_seed.py` before the
  server starts, so a fresh stack comes up migrated and seeded.
- Number each new revision one past the latest (`--rev-id 0002`), so files sort in apply order.
- Development data goes in `api/infrastructure/dev_data.py` with a fixed ID. If its table is not
  seeded yet, add the table to `SEED` in `dev_seed.py`, after the tables it refers to. The seed
  only inserts missing rows and never changes an existing one.
- With `DB_*` set, `pytest` also runs `tests/integration/test_migrations.py`, which upgrades,
  seeds and downgrades a throwaway database it creates and drops. Without them it is skipped.
- The health check reports the connection as `database`.

Naming, checked against every migration by `tests/unit/test_column_names.py`:

- **ID columns are `id` or `<entity>_id`**, named exactly after what they point at: `printer_id`,
  `print_job_id`, `fleet_section_id`. No prefixes (`assigned_printer_id`, `owner_user_id` are
  wrong). A second column pointing at the same entity is usually duplicated data; find its
  source instead.
- **An identifier from outside the database is `<name>_ref`**, such as `keycloak_user_ref` or
  `external_printer_ref`. `_id` always means a row in this schema.
- **The one exception** is a polymorphic pair, `target_type` beside `target_id`.
- **Each fact is stored once.** Who did something and when lives in the domain's event table,
  such as `print_job_events`, not copied onto the entity as `approved_by`/`approved_at`.
- **Timestamps use the `common.v1.TimeStatus` names:** `created_at` and `updated_at` on every
  table (only `created_at` on an append-only one), and `deleted_at` or `expires_at` where the
  row has that lifecycle.

Picture: `docs/database-schema.html`.

## Images

- A new path dependency goes in `pyproject.toml` **and** both `*.Dockerfile.dockerignore` files.
- Upgrading a codegen tool bumps its version and SHA-256 in `deploy.Dockerfile` together with
  the version `/onboarding` installs.
- The dev image holds only runtime dependencies: tests, lint and codegen run on the host. Saving
  under `api/` reloads in the container; changing `pyproject.toml`, `uv.lock` or a path package
  rebuilds the image, so rerunning codegen on the host after a `.proto` change is enough.
- The version is read from `pyproject.toml` at startup, so that file is deployed beside `api/`.
- Codegen runs through `uv run --project …` because the ConnectRPC generator,
  `protoc-gen-connectrpc`, is a dev dependency of `packages/proto/utils`, which holds the
  generated Python every app imports.

## API reference

`protoc-gen-connect-openapi` describes the Connect services during server codegen
(`api/gen/openapi/`), FastAPI describes the REST routes, and `api/common/openapi.py` merges them.
The result is served at `/api/openapi.json`, `/api/docs` (Swagger UI) and `/api/redoc`, under
the API prefix so the deployed reverse proxy forwards them, and `export_openapi.py` writes it into
`docs/api/` for `docs/api.html`. The pre-commit hook runs codegen and the export when files under
`api/`, `packages/proto/`, `pyproject.toml` or `buf.gen.server.yaml` are staged, stages the result,
and blocks the commit if it cannot. By hand:
`uv run --project apps/server python apps/server/export_openapi.py` (add `--check` to report stale
files without writing). Never edit `docs/api/`; a unit test fails if it does not match what the
server serves. Descriptions come from `.proto` comments and REST route docstrings.

## Logging

- Log through structlog with key-value pairs, never formatted strings:
  `structlog.stdlib.get_logger(__name__).info("printer claimed", printer_id=printer_id)`.
- `RequestContextMiddleware` binds `request_id` (a fresh UUID used only for logging, never read
  from or returned in a header), `method` and `path` (the procedure, for Connect), and logs one
  `request finished` line per request with `status` and `duration_ms`, replacing uvicorn's access
  log.
- `LOG_FORMAT` is `json` by default (the deploy image) or `console` (`infra/dev/compose.yaml`,
  `dev_run.py`).
- A processor added to `SHARED_PROCESSORS` in `api/logging_config.py` runs on every line,
  including uvicorn's and other libraries'. `lifespan.py` applies the configuration at startup,
  so the few lines uvicorn prints before then keep uvicorn's own format.

## Writing tests

Read `tests/AGENTS.md` before writing or changing a test here, including under `e2e/`. It sets the
standard for the server's tests. Where an existing test disagrees with it, follow `tests/AGENTS.md`.
