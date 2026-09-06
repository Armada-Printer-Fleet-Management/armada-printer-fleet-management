# `infra/compose/` — local backing services

Docker Compose definitions for the services a developer needs running locally, the Postgres
database first among them. `/onboarding` starts these before applying migrations.

**Belongs here:** compose files, and any seed or init scripts they mount.

Credentials belong in `.env` or `config/`, never in a committed compose file.
