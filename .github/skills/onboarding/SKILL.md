---
name: onboarding
description: "Set up a developer environment for this repository \u2014 install toolchain, wire git hooks, install dependencies, prepare config, run tests, start the app, and open the documentation. Use on a fresh clone, or when an environment is broken and needs re-establishing."
---
<!-- GENERATED FILE - DO NOT EDIT
     Source:    .claude/skills/onboarding/SKILL.md
     Generator: scripts/sync_agent_config.py -->

# Onboarding

Take a fresh clone to a working development environment, and leave the developer looking at the
running app and the documentation.

Run the steps in order. A step whose target does not exist in the repository is **not applicable** —
report it and move on. A step whose target exists but fails is a **failure** — stop, explain, and do
not press on, because later steps will fail confusingly.

Report a summary at the end: what was installed, what ran, what was skipped and why.

## 1. Check prerequisites

Report the version of each, and stop with installation guidance if one is missing:

| Tool | Check |
|---|---|
| Git | `git --version` |
| Node | `node --version` (22.13 or newer) |
| Python | `python --version` (3.13 or newer) |
| Docker | `docker --version` |

## 2. Install the toolchain

Check each before installing — never reinstall something already present.

| Tool | Purpose | Windows | Linux / macOS |
|---|---|---|---|
| `uv` | Python packages and virtualenv | `winget install astral-sh.uv` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| `pnpm` | Node packages | `npx get-pnpm` | `npx get-pnpm` |
| `buf` | Protobuf codegen and linting | `winget install bufbuild.buf` | `curl -sSL https://github.com/bufbuild/buf/releases/latest/download/buf-$(uname -s)-$(uname -m) -o /usr/local/bin/buf && chmod +x /usr/local/bin/buf` |
| `gitleaks` | Secret scanning in the pre-commit hook | `winget install gitleaks.gitleaks` | `brew install gitleaks` |

`pnpm` is installed with `npx get-pnpm`, the npm-based installer from <https://pnpm.io/installation>.
On Windows, run it from PowerShell rather than Git Bash. It needs Node 22.13 or newer.

`gitleaks` is required: without it the pre-commit hook cannot scan for secrets and will warn on
every commit.

Each `winget` install and `get-pnpm` edits `PATH`; open a new shell before the tools resolve.

If a package manager is unavailable, point the user at the project's releases page rather than
guessing an alternative install path.

## 3. Wire up git hooks

```
git config core.hooksPath .githooks
```

This is per-clone and is not inherited, so a fresh clone always needs it. Verify with
`git config core.hooksPath`, then confirm the hooks are executable.

## 4. Install dependencies

| Condition | Command |
|---|---|
| `pyproject.toml` exists | `uv sync` |
| `pnpm-workspace.yaml` exists | `pnpm install` |

## 5. Generate API code

If `buf.gen.yaml` exists:

```
buf generate
```

This produces the Python server interfaces and TypeScript clients from `packages/proto`. The output
is gitignored and must exist before anything type-checks.

## 6. Prepare configuration

For every `*.example.*` file under `config/`, and for `.env.example` at the root, create the real
file if it is missing by copying the example.

**Never overwrite an existing config file** — it holds the developer's own values.

Afterwards, list every file created and tell the user which values they must fill in themselves.
Placeholder values such as `REPLACE_ME` will not work.

## 6b. Configure the AI audit log

This project is coursework, and `.integrity/POLICY.md` requires that agent sessions be logged.
Two values in `.env` control it.

**`AI_AUDIT_LOG_DIR`** — ask the developer for the path, and tell them plainly:

> This must be the **OneDrive shortcut to the team's shared `ai-audit-log` directory**, not a
> folder on your machine. A local path will appear to work while logging nothing to anyone but
> you.

**`AI_AUDIT_AUTHOR`** — their name as `firstname.lastname`, matching the branch naming
convention. Suggest a value derived from `git config user.name`, but have them confirm it.

Write both into `.env`, then **prove it works** rather than assuming:

```
python scripts/export_ai_audit.py
```

A path that is set but wrong is worse than one that is unset, because nothing will complain
again. If the script reports a problem, fix it here — do not move on.

## 6c. Read the integrity policy

`.integrity/POLICY.md` is required reading before their first commit. Point them at it and
summarise the parts that change their daily work:

- AI-assisted commits carry an AI Use Statement; `/commit-message` composes it, and the
  developer writes the `Verified:` field themselves.
- Design decisions happen in plan mode, with options and trade-offs.
- Third-party library forks live in **sibling directories beside this repository, never inside
  it**. Some are confidential.
- Sponsor and personal data never go into a prompt.

Copilot sessions are not exported automatically. If they use Copilot, they run
`/export-ai-integrity` themselves.

## 6d. Connect Jira

Decisions are tracked in Jira. Agents read them through the official Atlassian MCP server.

**Claude Code** reads `.mcp.json` at the repository root and will ask the developer to approve
the server the first time they start a session. Have them approve it, then run `/mcp` and
complete the OAuth sign-in in the browser.

**Copilot CLI** has no repository-level MCP configuration — it is per-user. Copilot users run:

```
copilot mcp add --transport http atlassian https://mcp.atlassian.com/v2/mcp
```

Then ask for two values and write them into `.env`:

| Variable | Value |
|---|---|
| `JIRA_SITE_URL` | Their Atlassian site, e.g. `https://your-site.atlassian.net` |
| `JIRA_PROJECT_KEY` | The project abbreviation used in ticket IDs and branch names |

**Prove it works** rather than assuming. Ask the agent to call `getAccessibleAtlassianResources`
and confirm their site is listed. A connection that authenticates against the wrong site will not
complain later.

Neither value is ever committed. The repository holds only the generic endpoint.

## 7. Start backing services

If `infra/compose/` contains a compose file:

```
docker compose -f infra/compose/docker-compose.yml up -d
```

Wait for the database to accept connections before continuing. If `alembic.ini` exists, apply
migrations:

```
uv run alembic upgrade head
```

## 8. Run the tests

Run whichever apply, and report results honestly — including failures:

```
uv run pytest -q
pnpm -r test --run
```

A fresh clone should have passing tests. If they fail, that is a real problem worth surfacing, not
something to skip past.

## 9. Run the app

Skip this step if `--skip-app` was passed.

Start the server, then the web app, then the desktop app, each as configured in its own directory.
Report the URL for each. Leave them running.

## 10. Open the documentation

The docs are hand-written HTML and need no build step. Open `docs/index.html` in the default
browser:

- Windows: `start docs/index.html`
- macOS: `open docs/index.html`
- Linux: `xdg-open docs/index.html`

## 11. Summarise

Tell the developer:

- What was installed and what was already present
- Which steps were not applicable, and why
- Any config files they must fill in before the app will work
- Where the app and docs are running
- That `AGENTS.md` is the conventions they are expected to follow, and `HANDOFF.template.md` is
  what they copy to `HANDOFF.md` to track their own session state
- That `.integrity/POLICY.md` is required reading before their first commit, and whether their
  audit log exported successfully
- Whether Jira is connected, and that decision history is found by running `git blame` on the
  code and looking up the ticket from the commit message
