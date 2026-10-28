# `infra/dev/` — the local development stack

`compose.yaml` runs everything a developer needs in Docker: the server and web app with live
reload, plus Postgres, Garage and Keycloak. Start and stop it with the run script, which supplies
the settings file:

```
python scripts/compose_run.py dev          # build, start, and follow the logs
python scripts/compose_run.py dev down     # stop it; the databases and stored files are kept
```

| Service | Address | Notes |
|---|---|---|
| `server` | `http://127.0.0.1:8000` | `apps/server/dev.Dockerfile`, reloads on changes under `api/` |
| `web` | `http://127.0.0.1:5174` | `apps/web/dev.Dockerfile`, reloads on changes under `src/`; `/api` is forwarded to `server` and `/auth` to `keycloak` |
| `db` | `localhost:5432` | Postgres 17, user and database name `armada` |
| `garage-s3-storage` | `http://localhost:3900` | S3 API, bucket name `armada` |
| `keycloak` | `http://localhost:5174/auth` | Identity provider, realm `armada`. Also published at `localhost:8080` for debugging |
| `keycloak-db` | not published | Keycloak's own Postgres 17, user and database name `keycloak` |

Every port is bound to localhost, so nothing is reachable from the network. The settings,
including the generated Postgres password, Garage keys and Keycloak passwords, are in
`config/compose.dev.env`; see `config/compose.dev.example.env`. If a Postgres installed natively
on your machine already holds 5432, set `DB_PORT` there.

Both images copy in the generated API code from your machine, so run codegen before the first
start and after changing a `.proto` file. With the stack running, the regenerated code is synced
in automatically so you should only need to regenerate it, not re compose.

**Belongs here:** the development compose file, and any seed or init scripts it mounts. The
deployment stack is `infra/deploy/`.

Credentials belong in `config/`, never in a committed compose file.

## Keycloak

Use Keycloak through `http://localhost:5174/auth`, the web app's own address, as users will. It
builds its URLs and token issuer from the address it is reached on, so going through
`localhost:8080` gives tokens an issuer the rest of the stack does not expect.

- **Admin console:** `http://localhost:5174/auth/admin`, signing in with `KEYCLOAK_ADMIN_USERNAME`
  and `KEYCLOAK_ADMIN_PASSWORD` from `config/compose.dev.env`. This is the `master` realm, for
  operating Keycloak itself; switch to the `armada` realm with the dropdown at the top left.
- **Realm:** `infra/deploy/armada-realm.json` is imported on Keycloak's first start, and skipped
  once the `armada` realm exists. To load a changed file, delete only Keycloak's data and start
  again:

  ```
  python scripts/compose_run.py dev down
  docker volume rm armada-dev_keycloak_pgdata
  python scripts/compose_run.py dev
  ```
