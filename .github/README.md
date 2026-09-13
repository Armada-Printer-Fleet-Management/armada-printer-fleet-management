# .github

| Path | What it is |
|---|---|
| `workflows/` | CI and secret scanning |
| `actions/setup-buf/` | Pinned buf installer, used by the workflows |
| `skills/` | Generated Copilot project skills. Edit `.claude/skills/`, not these |
| `prompts/` | Generated Copilot prompt files. Edit `.claude/skills/`, not these |

## Branch protection

Rulesets are not configured through the settings UI. An admin applies them with:

```bash
scripts/apply_rulesets.sh <org>
```

The script is the definition of what is enforced — read it there. Re-running updates the existing
rulesets in place, so it is safe to run after any change.

**When adding a required status check**, confirm the job has reported on a real pull request
first. A job skipped by an `if:` condition reports no status at all, and requiring one that never
runs leaves every pull request pending with no way to merge and no obvious cause.
