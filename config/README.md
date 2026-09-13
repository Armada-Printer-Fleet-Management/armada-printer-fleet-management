# Configuration

All application logic in this repository is generic. Everything that differs between deployments
lives here: identity provider endpoints, branding tokens, database connection details, printer
inventories, environment URLs.

## The rule

**Files in this directory are gitignored by default.** Only two things are committed:

| Committed | Ignored |
|---|---|
| `something.example.yaml` | `something.yaml` |
| `README.md` | everything else |

Ignoring is the default so that adding a new configuration file and forgetting to ignore it
cannot leak a deployment's details. You have to opt *in* to publishing.

## Adding a new configuration file

1. Write `<name>.example.<ext>` with the full structure and **placeholder values only** — no real
   endpoints, tenant IDs, hostnames, or organisation names.
2. Document each field in that example file with a comment: what it is, whether it is required,
   and what a valid value looks like.
3. Copy it to `<name>.<ext>` locally and fill in real values. Git will ignore it.

## What must never appear in an `.example` file

Organisation names, real hostnames or domains, tenant or client IDs, database names, subnet
ranges, employee names, API keys.

**Use `localhost` for every host and URL.** If a placeholder needs explaining, explain it in a
comment rather than by using a real value.

## Secrets

Credentials do not belong in configuration files at all, example or otherwise. Use environment
variables, documented in `.env.example` at the repository root.
