# `plugins/` — the adapters

Implementations of the ports in `packages/plugin-api/`. Each one adapts a specific external
system to an interface the domain defined.

| Directory | What it adapts |
|---|---|
| `auth-oidc/` | Verifies access tokens from an OpenID Connect provider (`TokenVerifier`) |
| `identity-local/` | User and role lookup |
| `s3-file-store/` | File storage on any S3-compatible store, such as Garage |
| `theme-default/` | Branding and theme tokens |

**A plugin may not import another plugin, or anything in `apps/`.** Only `apps/` may construct
one, choosing it from the deployment's configuration; the server does this in `api/plugins.py`.
Its import-linter contracts check this for every plugin it installs.

This is what keeps a deployment-specific integration out of the domain: a particular identity
provider is a plugin pointed at different configuration, never a change to `core-domain/`.
