# `plugins/identity-keycloak/` — Keycloak accounts

Implements the `IdentityDirectory` port against Keycloak's Admin REST API.
`KeycloakIdentityDirectory` creates an account with a realm role, and deletes one.

It signs in as a confidential client's service account, using the client credentials grant. That
account needs the `realm-management` roles `manage-users`, `view-users` and `view-realm`.

The server passes in:

| Argument | What it is |
|---|---|
| `base_url` | Keycloak's address including any relative path, such as `http://keycloak:8080/auth` |
| `realm` | The realm the accounts live in |
| `client_id` | The confidential client whose service account makes the calls |
| `client_secret` | That client's secret |

A new account is enabled and has no password. If assigning its role fails, the account is deleted
before the error is raised. A duplicate email raises `AccountExistsError`; anything else Keycloak
refuses, or a Keycloak that cannot be reached, raises `IdentityDirectoryError`.

Tests run against a fake Keycloak through `httpx2.MockTransport`: `uv run pytest`.
