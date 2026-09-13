---
name: commit-message
description: "Compose a commit message that satisfies this repository's commit contract, from the working tree and a ticket reference. Returns the message text. Never commits or stages. Use when a commit message is needed, either directly or as a step inside another skill."
argument-hint: "[TICKET-ID] [ticket title]"
---

# Commit message

Compose a commit message in this repository's required format and return it.

**This skill never runs `git commit`, `git add`, or any command that writes.** It reads and
composes. Committing is the caller's decision.

## Inputs

| Input | Source | Required |
|---|---|---|
| Ticket ID | Argument, else parsed from branch name, else ask | Yes |
| Ticket title | Argument, else ask | Yes |
| Staged changes | `git diff --cached` | Yes |
| Unstaged changes | `git diff` and `git status --short` | Yes |

Invocation: `/commit-message <TICKET-ID> <Ticket title>`

Both arguments are optional at the call site. Resolve them in this order, and only fall through
when the previous source yields nothing:

1. **Arguments passed to this skill.** If a calling skill supplied them, use them as given. Do not
   re-derive or second-guess them.
2. **The branch name**, for the ticket ID only. Match `[A-Z][A-Z0-9]{1,9}-[0-9]+` anywhere in it.

   | Branch | Ticket |
   |---|---|
   | `developer/firstname.lastname/ABC-123-printer-polling` | `ABC-123` |
   | `feature/print-queue` | none — ask |

   Feature branches carry no ticket, so fall through to asking.
3. **Ask the user.** Offer a suggested title drawn from the diff, but the value is theirs to
   confirm — the trailer is meant to match Jira, which you cannot see.

Never invent a ticket ID. Never guess one from the diff.

## Required format

```
<type>(<scope>): <title>

- plain-language bullet
- one bullet per meaningful change

AI Use Statement
  Tool:     Claude Code (Opus 5)
  Mode:     Local
  Output:   what the agent produced
  Data:     none
  Verified: how the developer checked it

<TICKET-ID> <Ticket title>
```

The AI Use Statement block appears **only when an agent helped produce the change**. See
*The AI Use Statement*, below.

The ticket ID is your project's Jira abbreviation followed by a hyphen and the issue number —
whatever prefix this project uses. Take it from the input; do not substitute a placeholder.

## Reading the working tree

Always read both, before composing anything:

```
git diff --cached          # staged — what would actually be committed
git diff                   # unstaged — modified but not staged
git status --short         # includes untracked files
```

They serve different purposes:

- **Staged changes are what the message describes.** Only these land in the commit, so only these
  belong in the bullets.
- **Unstaged and untracked changes are context.** Use them to spot a problem the staged diff alone
  would hide: a change staged without its test, half a rename, a new file the staged code imports
  but that was never added.

If unstaged or untracked changes look like part of the same unit of work, **say so before returning
the message** and name the files. Let the user decide whether to stage them. Do not stage anything
yourself, and do not describe unstaged work in the bullets — the message must match the commit.

If nothing is staged but the working tree has changes, compose the message from those changes and
state plainly that nothing is staged yet, so the caller knows the message describes the working
tree rather than a prepared commit. If the tree is entirely clean, say so and stop.

## Composing

- **Type**: one of `feat fix docs style refactor perf test build ci chore revert`.
  Choose from what the diff actually does, not from what the ticket says.
- **Scope**: lowercase area touched — `printer`, `auth`, `ui`, `ci`. Omit if it spans many.
- **Title**: imperative mood, no trailing period, **whole subject line ≤ 72 characters**.
- **Bullets**: explain each change *to a human in simple terms* — what changed and why it matters,
  not which lines moved. One per meaningful change; skip formatting and other trivia.
- **Trailer**: the ticket ID and title as the final line, preceded by a blank line.
- **Never emit a `Co-Authored-By` trailer.** The `commit-msg` hook rejects it. Agent involvement
  is declared in the AI Use Statement instead — disclosure of use and claim of authorship are
  different things, and only the first belongs here.

If the staged changes cover two unrelated concerns, note it and suggest splitting into separate
commits — but return a message for what is actually staged.

## The AI Use Statement

Required by `.integrity/POLICY.md` §3 on any commit an agent helped produce. Field definitions
are in `.integrity/AI-USE-STATEMENT.md`; this is how to compose one.

Place it after the bullets and before the ticket trailer, separated by blank lines, with the
field values aligned:

```
AI Use Statement
  Tool:     Claude Code (Opus 5)
  Mode:     Local
  Output:   parser for the printer status payload, plus its unit tests
  Data:     none
  Verified: ran the tests and compared the field names against the
            vendor's HTTP API documentation
```

| Field | How to fill it |
|---|---|
| Tool | The product and model you actually are. `Claude Code (Opus 5)`, `Copilot CLI (Sonnet 5)`. |
| Mode | `Web`, `Desktop`, or `Local`. |
| Output | What you produced in this session, concretely and in past tense. One line. |
| Data | Normally `none`. Name any anonymisation if there was some. |
| Verified | **Ask the developer. See below.** |

### Never write the `Verified:` field

Ask the developer how they checked the work, and wait for their answer.

Do not infer it from the session. Do not write "verified by inspection", "tests pass", or
anything else you worked out yourself. Do not offer a draft for them to approve — an answer
that originated with you is worthless even if they accept it, because the field exists to
record a human's assurance and there would not be one.

**If they have not verified the work, the commit is not ready.** Say that, and return no
message. That is the honest outcome, and it is the whole point of the field.

### Omit the block entirely when no agent helped

Disclosure is opt-in and nothing enforces it. If the developer wrote the change themselves,
there is no statement — adding one would be a false declaration in the other direction. Ask if
it is unclear.

### This text is published

The commit lands in a repository that becomes public. Generalise every sponsor, vendor,
organisation and person: "a partner's identity provider", never the vendor's name; "the
sponsor's parts database", never the organisation's. The audit log in OneDrive holds the
unabridged record — the commit message does not need it.

Keep the whole block to five lines. It is a declaration, not a report.

## Cherry-picks onto a release branch

A fix backported to a release branch is a **clone ticket**, and its message keeps the original
commit's message intact, adds the source hash, and ends with the clone's own ticket:

```
<Original Commit Message>

Cherry-picked from <commit-hash>

<Clone Ticket ID> <Clone Title>
```

When composing one:

- Reuse the original subject and bullets verbatim. Do not rewrite them — the point is that the two
  commits are recognisably the same change.
- Take the hash from the original commit on `main`, abbreviated as `git log` shows it.
- Use the **clone** ticket in the trailer, not the original.
- If the pick had conflicts or needed adjustment, add a bullet saying what changed and why. That
  record is the reason clone tickets exist.

## Export the audit log

After composing the message, run:

```
python scripts/export_ai_audit.py
```

Composing a commit message means a unit of work is finished, which is the moment the session
is worth exporting. Report anything it says, and if it reports that the audit log is not
configured, pass that on rather than burying it — the developer needs to run `/onboarding`.

This does not block the message. Return it either way.

## Output

**Called directly by a user** — print the composed message to the terminal in a fenced block, ready
to copy or hand to `git commit -F`. Do not run the commit.

**Called by another skill or agent** — return the message text as this skill's result, with no
surrounding commentary, formatting, or explanation. The caller consumes it as input.

## Example

Illustrative only — use this project's own ticket abbreviation, not `ABC`.

```
feat(printer): add Moonraker status polling

- Poll each configured printer every 5 seconds for state and temperature
- Show printers that stop responding as offline instead of silently stale
- Make the interval configurable so slow networks can back off

AI Use Statement
  Tool:     Claude Code (Opus 5)
  Mode:     Local
  Output:   the polling loop, offline detection, and their unit tests
  Data:     none
  Verified: ran the tests against a local mock printer and checked the
            response fields against the vendor's HTTP API documentation

ABC-42 Add printer status polling
```

The same commit written without an agent carries no statement block at all.
