# `plugins/auth-oidc/` — OIDC authentication

Implements the authentication port against any OpenID Connect provider.

The provider is **configuration, not code**. Endpoints, client IDs and scopes come from
`config/`, which is gitignored by default. Pointing this at a particular vendor is a config
file, never an edit here — that is what lets this repository be published.
