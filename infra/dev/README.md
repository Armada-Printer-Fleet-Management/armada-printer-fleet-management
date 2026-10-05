# `infra/dev/` — the local development stack

`compose.yaml` runs everything a developer needs in Docker: the server and web app with live
reload, plus Postgres and Garage. Start and stop it with the run script, which supplies the
settings file:

```
python scripts/compose_run.py dev          # build, start, and follow the logs
python scripts/compose_run.py dev down     # stop it; the database and stored files are kept
```

| Service | Address | Notes |
|---|---|---|
| `server` | `http://127.0.0.1:8000` | `apps/server/dev.Dockerfile`, reloads on changes under `api/` |
| `web` | `http://127.0.0.1:5174` | `apps/web/dev.Dockerfile`, reloads on changes under `src/`; `/api` is forwarded to `server` |
| `db` | `localhost:5432` | Postgres 17, user and database name `armada` |
| `garage-s3-storage` | `http://localhost:3900` | S3 API, bucket name `armada` |

Every port is bound to localhost, so nothing is reachable from the network. The settings,
including the generated Postgres password and Garage keys, are in `config/compose.dev.env`; see
`config/compose.dev.example.env`. If a Postgres installed natively on your machine already holds
5432, set `DB_PORT` there.

Both images copy in the generated API code from your machine, so run codegen before the first
start and after changing a `.proto` file. With the stack running, the regenerated code is synced
in automatically so you should only need to regenerate it, not re compose.

**Belongs here:** the development compose file, and any seed or init scripts it mounts. The
deployment stack is `infra/deploy/`.

Credentials belong in `config/`, never in a committed compose file.
