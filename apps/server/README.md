# `apps/server/` — the backend service

Python, ASGI, ConnectRPC. Serves the contract in `packages/proto/` to both the web and desktop
applications.

- How a request moves through it: [`docs/domain-architecture.html`](../../docs/domain-architecture.html)
- The rules for working in it: [`AGENTS.md`](AGENTS.md)
- Every endpoint: [`docs/api.html`](../../docs/api.html), or `/api/docs` on a running server

## Running it

The server runs in Docker by default, as part of the development stack in `infra/dev/` alongside
the web app, Postgres, Garage and Keycloak. Generate the code first, and again after changing a
`.proto` file. From the repo root, with Docker running:

```
uv run --project packages/proto/utils python scripts/generate_proto.py buf.gen.python.yaml
uv run --project apps/server python scripts/generate_proto.py buf.gen.server.yaml
python scripts/compose_run.py dev
```

This serves `http://127.0.0.1:8000`, reachable from this machine only, and follows the logs. `Ctrl+C` stops it;
`python scripts/compose_run.py dev down` removes the containers.

To build the image that ships:

```
docker build -f apps/server/deploy.Dockerfile -t armada-server .
```

## Running natively

```
uv sync --project apps/server
uv run --project packages/proto/utils python scripts/generate_proto.py buf.gen.python.yaml
uv run --project apps/server python scripts/generate_proto.py buf.gen.server.yaml
python apps/server/dev_run.py          # add --dev to reload on changes
```

Both ways use port 8000, so run one at a time. Natively, set the database and file store
settings in your shell first. Against the dev stack:

| Variable | Value |
|---|---|
| `DB_HOST` | `127.0.0.1`, not `localhost`: Postgres is published on IPv4 only, and `localhost` can hang trying IPv6 |
| `DB_PORT` | Optional; `5432`, or `DB_PORT` from `config/compose.dev.env` if set |
| `DB_NAME` | `armada` |
| `DB_USER` | `armada` |
| `DB_PASSWORD` | `DB_PASSWORD` from `config/compose.dev.env` |
| `FILE_STORE_BACKEND` | Optional; `s3` is the default and the only plugin today |
| `FILE_STORE_ENDPOINT_URL` | `http://localhost:3900` |
| `FILE_STORE_REGION` | `garage` |
| `FILE_STORE_BUCKET` | `GARAGE_DEFAULT_BUCKET` from `config/compose.dev.env` |
| `FILE_STORE_ACCESS_KEY` | `GARAGE_DEFAULT_ACCESS_KEY` from `config/compose.dev.env` |
| `FILE_STORE_SECRET_KEY` | `GARAGE_DEFAULT_SECRET_KEY` from `config/compose.dev.env` |

It also needs where to check access tokens, against the dev stack's Keycloak:

| Variable | Value |
|---|---|
| `AUTH_ISSUER` | `http://localhost:5174/auth/realms/armada`, the address tokens are issued for |
| `AUTH_JWKS_URL` | `http://localhost:8080/auth/realms/armada/protocol/openid-connect/certs`, where the signing keys are fetched |
| `AUTH_BACKEND` | Optional; `oidc` is the default and the only plugin today |
| `AUTH_AUDIENCE` | Optional; defaults to `armada-server` |
| `AUTH_ROLES_CLAIM` | Optional; defaults to `realm_access.roles`, where Keycloak puts realm roles |
| `AUTH_ENFORCE` | Optional; `false` by default. See "Access tokens" in [`AGENTS.md`](AGENTS.md) |

## Database

The dev stack migrates and seeds itself on start. After adding a migration or seed data, apply it
to the running stack from the repo root:

```
docker compose -f infra/dev/compose.yaml --env-file config/compose.dev.env run --rm --build migrate
```

Natively, with `DB_*` set, from `apps/server`:

```
uv run alembic upgrade head
uv run python dev_seed.py
uv run alembic revision --rev-id 0002 -m "describe the change"   # a new, empty migration
```

## Tests

```
uv run --directory apps/server pytest
```

Add `tests/unit` or `tests/integration` to run one suite. Before writing or changing a test, read
the rules in [`tests/AGENTS.md`](tests/AGENTS.md). They apply to everyone, not only agents.
[`docs/testing.html`](../../docs/testing.html) has the short, visual version.
