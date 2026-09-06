---
name: export-ai-integrity
description: "Export agent session transcripts to the team's AI audit log and collect the developer's human-verification answer for each one. Use at the end of a working session, before composing a commit message, or after a Copilot session, which is not exported automatically."
argument-hint: "[session-id]"
---

# Export AI integrity log

Copy this repository's agent session records to the team's shared audit log, then ask the
developer for the one field no agent may write.

Required by `.integrity/POLICY.md`. The log and the AI Use Statements in commit messages are
together the evidence that this project's AI use was disclosed and checked.

## 1. Run the export

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

## 2. Collect the verification answers

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

## 3. Point the ticket at the log

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

## 4. Report

Tell the developer:

- Where the log was written
- How many sessions were exported, and how many were unchanged
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
