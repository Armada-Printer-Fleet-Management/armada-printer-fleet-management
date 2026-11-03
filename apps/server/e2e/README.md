# Server end-to-end smoke tests

Smoke tests that act as real users against a deployed, prod-like server. Nothing is mocked: each
test signs in through Keycloak and calls the server over the network, as the web and desktop apps
do. The rules for what belongs here are in [`../tests/AGENTS.md`](../tests/AGENTS.md).

```
uv run --directory apps/server pytest e2e
```

The default `pytest` run does not include this folder; it runs only when named.

## Configuration

The suite reads its target from environment variables. There are no defaults, and a missing value
fails every test with the names of the variables to set.

| Variable | What it is |
| --- | --- |
| `E2E_SERVER_URL` | The server's public address, without `/api`, such as `http://localhost` for a local deploy stack |
| `E2E_AUTH_ISSUER` | The realm's issuer, which must match the server's `AUTH_ISSUER`, such as `http://localhost/auth/realms/armada` |
| `E2E_AUTH_CLIENT_ID` | The e2e client in that realm, created below |
| `E2E_AUTH_CLIENT_SECRET` | That client's secret, from its **Credentials** tab |
| `E2E_STUDENT_USERNAME`, `E2E_STUDENT_PASSWORD` | A test user with the `student` role |
| `E2E_STAFF_USERNAME`, `E2E_STAFF_PASSWORD` | A test user with the `staff` role |

These are credentials, so they stay in your shell or in CI secrets, never in a committed file.
Never point the suite at production.

## Preparing a target

The suite signs in with a password grant, which the shipped `armada-web` client does not allow.
Each target therefore needs its own **e2e client** and **test users**, created in that target's
Keycloak and nowhere else. Never add them to `infra/deploy/armada-realm.json`, which ships to
production.

For a local deploy stack:

1. Add `AUTH_ISSUER=http://localhost/auth/realms/armada` to `config/compose.deploy.env`, then start
   the stack with `python scripts/compose_run.py deploy --domain :80 --admin-email you@example.com`.
   Without it, the server expects `https://:80/...` as the issuer and rejects every token with 401.
2. Open `http://localhost:8080/auth/admin` and sign in with `KEYCLOAK_ADMIN_USERNAME` and
   `KEYCLOAK_ADMIN_PASSWORD` from `config/compose.deploy.env`. The public address hides the admin
   console on purpose. On a remote machine, reach that port through an SSH tunnel. Switch to the
   `armada` realm.
3. **Clients → Create client**, named `armada-e2e`:
   - **Client authentication** on, so the client is confidential and has a secret.
   - **Direct access grants** on, and every other flow off.
   - Under **Client scopes → armada-e2e-dedicated**, add an **Audience** mapper that includes
     `armada-server` in the access token, as `armada-web` has. Without it the server rejects the
     token.
4. **Users → Add user** twice, such as `e2e-student` and `e2e-staff`. Fill in an email address at
   `example.com`, a first name and a last name, and turn **Email verified** on. Keycloak's user
   profile requires all three, and a password grant is refused with `invalid_grant` while any is
   missing. Set a password under **Credentials** with **Temporary** off, and assign the `student`
   or `staff` realm role under **Role mapping**.

## Adding a smoke test

A smoke test follows one key user flow. Its docstring starts "As a <role>, I ...", and it lives in
a `test_<flow>.py` file of its own. Endpoint responses and edge cases belong in the unit and
integration suites instead.

- Call the server through `as_student` / `as_staff` (Connect, signed in as that role), `health`,
  or `rest` for REST routes such as file uploads. To reach another Connect service, add its client
  to `SignedIn` in `conftest.py`.
- Create every record the test uses. Deployments are not seeded, so never rely on development data.
- Use made-up data only: `example.com` addresses and tiny files.

### A flow that is not finished yet

When a flow depends on a component still in development, mark the test rather than leaving it
failing:

```python
@pytest.mark.xfail(strict=True, reason="needs the server to map signed-in users to accounts")
```

The suite then passes while the flow is unfinished. `strict=True` makes it fail as soon as the
flow starts working, so whoever finishes the feature removes the mark in the same change.
