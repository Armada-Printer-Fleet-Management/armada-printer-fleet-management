# `plugins/` — the adapters

Implementations of the ports in `packages/plugin-api/`. Each one adapts a specific external
system to an interface the domain defined.

| Directory | What it adapts |
|---|---|
| `auth-oidc/` | Authentication against an OIDC provider |
| `identity-local/` | User and role lookup |
| `theme-default/` | Branding and theme tokens |

**A plugin may not import another plugin, or anything in `apps/`.** Only `apps/` may construct
one.

This is what keeps a deployment-specific integration out of the domain: a particular identity
provider is a plugin pointed at different configuration, never a change to `core-domain/`.
