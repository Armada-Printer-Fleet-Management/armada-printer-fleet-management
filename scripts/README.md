# `scripts/` — repository tooling

Maintenance scripts that run outside the applications.

| Script | What it does |
|---|---|
| `sync_agent_config.py` | Generates `.github/skills/`, `.github/prompts/`, and the `CLAUDE.md` import stubs from the canonical sources. Run it after editing a skill. |
| `export_ai_audit.py` | Exports agent session transcripts to the team's audit log. |
| `apply_rulesets.sh` | Applies branch protection rulesets to the GitHub repository. Needs admin rights. |

**Standard library only.** These run from git hooks and on fresh clones, before `uv sync` has
installed anything, so a script that imports a dependency fails exactly when it is most needed.
