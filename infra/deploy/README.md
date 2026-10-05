# `infra/deploy/` — deployment to on-premise hosts

The stack every deployed machine runs: testing, staging and every user installation alike. They
differ only in their environment file.

| File | What it is |
|---|---|
| `compose.yaml` | The four services: `web` (Caddy plus the built frontend), `server`, `db` (Postgres) and `garage-s3-storage` (S3 file storage). Images are pulled, never built here |
| `Caddyfile` | Baked into the web image. Serves the frontend, forwards `/api` to the server, and obtains HTTPS certificates for `DOMAIN` |
| `garage.toml` | Garage's configuration, mounted into its container. Single node, sqlite metadata, no replication |

Only ports 80 and 443 are published. Postgres and Garage are reachable from the other containers
and nowhere else.

**Never run `docker compose down -v`** on a deployed machine. It deletes the database, the stored
files and Caddy's certificates; re-requesting certificates repeatedly can hit Let's Encrypt's rate
limits.

## Running it without a registry

Until images are published, `python scripts/compose_run.py deploy` builds both deploy images
locally, tags them with the names `compose.yaml` expects, and starts the stack. Settings, including
generated secrets, are in `config/compose.deploy.env`; see `config/compose.deploy.example.env`.
For local testing, `--domain :80` serves plain HTTP with no certificate, so the admin email is
not used and any address works. A real domain gets an HTTPS certificate, and the email becomes
its expiry contact.

```
python scripts/compose_run.py deploy --domain :80 --admin-email admin@localhost
python scripts/compose_run.py deploy down
```

`--domain :80` serves plain HTTP, for a test machine without DNS. A real domain that resolves to
the machine gets an HTTPS certificate automatically.

**Belongs here:** the generic mechanism: how a release is installed, started and upgraded.

**Does not belong here:** any particular site's hostnames, certificates or credentials. Those
are configuration, supplied per deployment.
