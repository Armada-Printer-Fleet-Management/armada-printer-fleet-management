---
description: "Export agent session transcripts to the team's AI audit log and collect the developer's human-verification answer for each one. Use at the end of a working session, before composing a commit message, or after a Copilot session, which is not exported automatically."
---
<!-- GENERATED FILE - DO NOT EDIT
     Source:    .claude/skills/export-ai-integrity/SKILL.md
     Generator: scripts/sync_agent_config.py -->

# Export AI integrity log

Copy this repository's agent session records to the team's shared audit log, then ask the
developer for the one field no agent may write.

Required by `.integrity/POLICY.md`. The log and the AI Use Statements in commit messages are
together the evidence that this project's AI use was disclosed and checked.

## 1. Exclude confidential sessions

Sessions holding confidential Prusa Connect Local beta material are never exported; see the
_Confidential beta_ section of `AGENTS.md`.

Run `python scripts/export_ai_audit.py --dry-run`. Only the sessions it marks `exporting` are new
or changed since the last export, so ask only about those. If none are marked, skip to step 2.
Otherwise name just those sessions and ask the developer:

> Did any of these sessions use or mention non-public Prusa Connect Local beta material?

If they say yes, let them pick, and exclude each one:

```
python scripts/export_ai_audit.py --exclude <session-id> --reason "<their reason, in their words>"
```

A reason is required. The ID and reason are kept only in the git-ignored
`.integrity/excluded-sessions.local.txt`, and any copy already in the shared log is deleted.
`INDEX.md` then lists the session as excluded, without the reason or any content.

**Never open a transcript to decide, and never write the reason yourself.** Whether a session
held beta material, and why it is excluded, is the developer's answer.

Nothing excludes a session automatically. Exclude it **before it ends**; otherwise the
`SessionEnd` hook has already copied it to the shared log, and only the next run deletes it. When
the script reports a removal, tell the developer to empty the OneDrive recycle bin as well.

## 2. Run the export

```
python scripts/export_ai_audit.py
```

Pass `--session <id>` through if the developer named one.

The script copies records for this repository from Claude Code, Copilot CLI, and anything
listed in `AI_AUDIT_EXTRA_SOURCES`. It is keyed by session id and overwrites in place, so
running it repeatedly is safe and cheap.

**If it reports that the audit log is not configured, stop.** Do not work around it, do not
export somewhere else, and do not carry on as though the session were logged. Tell the
developer to run `/onboarding` to set `AI_AUDIT_LOG_DIR` and `AI_AUDIT_AUTHOR`. An unconfigured
machine produces no evidence, which is the failure this whole system exists to prevent.

## 3. Collect the verification answers

The script reports how many sessions still need one. Each is a `SESSION.md` whose
**Human verification** field holds an `UNFILLED` marker.

Ask the developer:

> How did you check the output of this session? Tests run, documentation compared, code traced
> by hand, tried against real hardware?

Pass their answer back through the script rather than editing `SESSION.md` by hand:

```
python scripts/export_ai_audit.py --verified "<their answer, in their words>"
```

Add `--session <id>` to answer for one session rather than all outstanding ones.

The script will not overwrite a session that already has an answer, so this is safe to repeat.
Editing `SESSION.md` directly is not — it puts an agent's hands on the one field that must not
have them.

### This is the part that matters

**Never write this field yourself.** Not a summary of the session, not an inference from what
the transcript shows, not "reviewed by inspection", not a helpful suggestion the developer can
edit. An agent that fills it in has fabricated a human's assurance, which is worse than leaving
it blank.

If the developer does not answer, leave the marker in place and say the session is still
unverified. That is an honest state and the script will keep reporting it.

If they answer for some sessions and not others, fill in the ones they answered.

Do not offer a draft answer for them to approve. The field is worthless if its content
originated with the agent.

## 4. Point the ticket at the log

If the branch names a ticket, add a comment to it saying where the session was exported. This is
what ties a transcript to the work it belongs to.

```
AI session log

  Session:  <date>_<tool>_<session-id8>
  Location: ai-audit-log/<author>/<date>_<tool>_<session-id8>/
  Contents: <the files the export wrote>
```

**Never attach the transcript itself.** Jira's storage is limited and these files run to
megabytes. The comment is a pointer to the shared audit log, and nothing more.

Give the path **relative to the shared `ai-audit-log` root**, not the absolute path on this
machine. Teammates navigate to it from their own OneDrive shortcut, where a local path means
nothing.

Skip this step when the branch carries no ticket — `main`, a feature branch, or exploratory work.
The export still happened and is still complete; there is simply nowhere to point.

## 5. Report

Tell the developer:

- Where the log was written
- How many sessions were exported, and how many were unchanged
- How many were excluded, and any copies removed from the log
- How many still need a verification answer, and which ones
- Whether a ticket comment was added, or why it was skipped

## When this runs

| Trigger | How |
|---|---|
| A Claude Code session ends | Automatic, via the `SessionEnd` hook in `.claude/settings.json`. Exports only; collects no answers, since nobody is there to ask. |
| Composing a commit message | `/commit-message` runs the export as its last step |
| A Copilot session ends | **Manually — nothing else will do it.** Copilot cannot trigger the hook. |
| On demand | This skill |

Because the automatic export cannot ask questions, verification answers accumulate as
outstanding until someone runs this skill. That is expected; the script keeps counting them.
