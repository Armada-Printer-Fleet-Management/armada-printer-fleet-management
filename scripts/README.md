# `scripts/` — repository tooling

Maintenance scripts that run outside the applications.

| Script | What it does |
|---|---|
| `sync_agent_config.py` | Generates `.github/skills/`, `.github/prompts/`, and the `CLAUDE.md` import stubs from the canonical sources. Run it after editing a skill. |
| `export_ai_audit.py` | Exports agent session transcripts to the team's audit log. |
| `apply_rulesets.sh` | Applies branch protection rulesets to the GitHub repository. Needs admin rights. |
| `generate_proto.py` | Runs `buf generate` for one template, prepending a local npm plugin's `.bin/` to `PATH` when `--node-modules` is given. Shared by every app/service that generates code from `packages/proto`. |
| `install_nsis.py` | Installs the pinned NSIS version that builds the desktop app's Windows installer, after checking its SHA-256. Windows only; shows one administrator prompt. Used by `/onboarding` and CI. |

## `generate_proto.py` usage

Run from the repo root. `buf` finds each template's local plugins on `PATH`, so the command
depends on where those plugins are installed. Every template sets `clean: true`, so buf deletes the
template's output folders before generating and removed protos leave no stale code behind.

| Template | Command | Why |
|---|---|---|
| `buf.gen.python.yaml` | `uv run --project packages/proto/utils python scripts/generate_proto.py buf.gen.python.yaml` | One Python copy for every app. `protoc-gen-connectrpc` is a dev dependency of `packages/proto/utils`; `uv run` puts it on `PATH`. |
| `buf.gen.server.yaml` | `uv run --project apps/server python scripts/generate_proto.py buf.gen.server.yaml` | The server's API documentation data only. |
| `buf.gen.desktop_ts.yaml` | `python scripts/generate_proto.py buf.gen.desktop_ts.yaml --node-modules apps/desktop/frontend/node_modules` | `protoc-gen-es` is an npm package in the frontend. |

## `install_nsis.py` usage

Run from the repo root on Windows. `python scripts/install_nsis.py --help` prints the full usage.

**Standard library only.** These run from git hooks and on fresh clones, before `uv sync` has
installed anything, so a script that imports a dependency fails exactly when it is most needed.
