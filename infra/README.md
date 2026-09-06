# `infra/` — deployment and backing services

How the applications run outside a developer's terminal. Deployment targets are on-premise
Linux machines.

| Directory | What it is |
|---|---|
| `compose/` | Docker Compose for local backing services |
| `deploy/` | Deployment manifests and host configuration |

Nothing here is environment-specific. Hostnames, credentials and certificates are configuration
under `config/`, gitignored by default.
