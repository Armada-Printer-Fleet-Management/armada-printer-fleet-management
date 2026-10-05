# `infra/` — deployment and backing services

How the applications run outside a developer's terminal. Deployment targets are on-premise
Linux machines.

| Directory | What it is |
|---|---|
| `dev/` | The local development stack: server and web with live reload, Postgres, Garage |
| `deploy/` | The deployment stack, its Caddyfile for hosting and Garage configuration for S3 data management |

Start or stop either stack with `python scripts/compose_run.py <dev|deploy> [up|down]`. The
deploy stack also needs `--domain` and `--admin-email` on its first run; `--domain :80` serves
plain HTTP for local testing.

Nothing here is environment-specific. Hostnames, credentials and certificates are configuration
under `config/`, gitignored by default.
