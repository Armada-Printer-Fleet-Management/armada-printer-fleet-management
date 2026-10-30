# `plugins/auth-oidc/` — OIDC access tokens

Implements the `TokenVerifier` port against any OpenID Connect provider. `OidcTokenVerifier`
checks an access token's RS256 signature against the provider's published keys, its issuer,
audience and expiry, and returns its subject and roles.

The provider is **configuration, not code**. The server passes in:

| Argument | What it is |
|---|---|
| `issuer` | The `iss` every token must carry: the provider's public address |
| `audience` | A value the token's `aud` must contain |
| `jwks_url` | Where to fetch the signing keys. It may be an internal address, so OIDC discovery is not used: a provider reports its issuer as whatever host asked |
| `roles_claim` | A dotted path to the roles list, such as `realm_access.roles` |

Keys are fetched on first use and cached. A token signed with an unknown key ID refetches them
once, which is how key rotation arrives. A rejected token raises `InvalidTokenError`; a provider
that cannot be reached, or serves no usable keys, raises `TokenVerifierError`.

Tests run against a fake provider through `httpx2.MockTransport`: `uv run pytest`.
