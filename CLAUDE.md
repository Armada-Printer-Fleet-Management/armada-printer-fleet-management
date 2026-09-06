@AGENTS.md

## Claude Code

The instructions above are the project's, shared with every assistant. This section is for Claude
Code only.

`AGENTS.md` is the canonical file. Claude Code does not read `AGENTS.md`, so this file imports it —
an import rather than a symlink because symlinks need Administrator rights or Developer Mode on
Windows, and this team is on Windows.

**Put project instructions in `AGENTS.md`, not here.** Anything written below this line is invisible
to Copilot and to every other assistant.

- Skills live in `.claude/skills/`. They are the source for the Copilot skill and prompt files
  under `.github/skills/` and `.github/prompts/`, which `scripts/sync_agent_config.py` generates.
  Edit the skill, never the generated file.
- Use plan mode for changes to `packages/plugin-api/` and `packages/core-domain/`. Both are
  depended on by every other package, so a change there is wider than it looks.
