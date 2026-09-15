# Agent Instructions

**This file is canonical.** Project instructions go here, not anywhere else.

`AGENTS.md` is the cross-tool standard: Copilot, Cursor, Codex, Gemini CLI, Aider and others read
it directly. Claude Code does not, so the `CLAUDE.md` beside it imports this file with `@AGENTS.md`
and adds a short Claude-only section.

Skills in `.claude/skills/` are the source for the Copilot skill and prompt files in
`.github/skills/` and `.github/prompts/`, which `scripts/sync_agent_config.py` generates. Edit
the skill, never the generated file.

> **Finding why code is the way it is.** Decisions are not recorded in this repository. Every
> commit carries the ticket it was made under, so the history is the index: `git log` or
> `git blame` the code, read the commit message, take the ticket ID from its final line, and
> read that ticket in Jira with the Atlassian MCP server.
>
> Do not add decision records to the tree, and do not cite ticket IDs in code or documentation —
> the commit already holds it. If a rule below looks wrong, find the commit that introduced it
> before changing it; it was decided deliberately.

---

## Must read: `.integrity/POLICY.md`

**Read [`.integrity/POLICY.md`](.integrity/POLICY.md) before working in this repository.** This
is a university capstone project, and its use of AI assistants is governed by the course's
academic integrity rules. The policy is short and every rule in it is actionable.

The three that change what you do most often:

- **Design work starts in plan mode.** Anything shaping the system rather than implementing it
  gets a survey of options with trade-offs, and the developer chooses. If a session opens with
  significant scope and plan mode is off, turn it on. See _Plan mode_, below.
- **AI-assisted commits carry an AI Use Statement.** `/commit-message` composes it.
  The `Verified:` field is written by the developer and **never** by an agent.
- **Sessions are exported to the team's audit log.** Configured by `/onboarding`, run by
  `scripts/export_ai_audit.py`.

---

## What this project is

Fleet management software for 3D printers, built as a university capstone project.

A monorepo delivering three applications, deployed to on-premise Linux machines:

| App         | Path            | Stack                                             |
| ----------- | --------------- | -------------------------------------------------- |
| Server      | `apps/server/`  | Python, ASGI, ConnectRPC                          |
| Web app     | `apps/web/`     | React + TypeScript + Vite                         |
| Desktop app | `apps/desktop/` | Python backend (pywebview) with a React frontend  |

The web and desktop apps are **different applications**. They talk to each other only through the
server. They share code through `packages/ui-kit` and `packages/api-client`, never by importing
each other.

---

## Architecture: ports and adapters

Dependencies point **inward only**. This is enforced by `import-linter` in CI — a violation is a
build failure, not a review comment.

```
L0  packages/proto/        .proto contract. No dependencies.
L1  packages/core-domain/  Pure domain logic. NO I/O, NO framework imports, NO network.
                           This is business logic that can be reused by multiple applications and layers if needed. Each core domain should be testable and isolated.
L2  packages/plugin-api/   PORTS — Protocol classes (Python) and interfaces (TS).
L3  plugins/*              ADAPTERS — implementations of those ports.
L4  apps/*                 COMPOSITION ROOTS — wire adapters to ports, expose services.
```

**Rules:**

- `core-domain` may not import from `plugin-api`, `plugins`, or `apps`.
- `plugins/*` may not import from each other or from `apps/*`.
- Only `apps/*` may construct concrete adapters. Everything else depends on the port.
- Never add a framework import to `core-domain`. If domain logic seems to need I/O, it needs a port.

---

## Open core: all logic here is generic

This repository is private today and becomes public after formal sign-off. That flip is a
visibility toggle, not a history-scrubbing exercise, because of one rule:

> **Every line of logic in this repository is generic. Anything specific to a particular
> deployment — an organisation, a vendor, an environment — is configuration, not code.**

There is no company-specific implementation to hide, because there isn't one. A Microsoft Entra
deployment is `auth-oidc` pointed at Entra's endpoints. A partner's branding is `theme-default`
loading a different token file. Their user database is `identity-local`'s external adapter with a
different mapping.

### How configuration works

- Configuration lives under `config/` and is **gitignored by default**.
- Commit a `*.example.*` sibling documenting each file's shape, with placeholder values.
- Ignoring is the default so that forgetting to ignore a new config file cannot leak it.
- Anything under a `private/` directory, or named `*.private.*` / `*.local.*`, is ignored anywhere
  in the tree.

**Before writing any file, ask: would this be safe on a public GitHub repo?** If the answer is no,
it is configuration and belongs under `config/`, not in code.

If a requirement genuinely cannot be expressed as configuration, that is a design problem to raise
before writing it — not a reason to hardcode an organisation's name.

---

## Commit contract

Commits that do not match this are **rejected by `.githooks/commit-msg`**.

```
<type>(<scope>): <title>

- plain-language bullet explaining a change
- one bullet per meaningful change

AI Use Statement
  Tool:     Claude Code (Opus 5)
  Mode:     Local
  Output:   what the agent produced
  Data:     none
  Verified: how the developer checked it

<Ticket ID> <Jira Ticket Title>
```

- `type` is one of: `feat fix docs style refactor perf test build ci chore revert`
- Subject line: max 72 characters, imperative mood, no trailing period.
- Body bullets explain changes **to a human in simple terms** — what changed and why, not a
  restatement of the diff.
- Final line is the Jira ticket ID and title. The ID is parsed from the branch name.
- **Never emit a `Co-Authored-By:` trailer.** The hook rejects it.
- **The AI Use Statement is included only when an agent helped**, and is omitted entirely
  otherwise. Nothing enforces it — a commit written unaided should not carry one. Format and
  field meanings: `.integrity/AI-USE-STATEMENT.md`.
- **`Verified:` is written by the developer, never by an agent.**

Use `/commit-message` to generate a compliant message.

---

## Branching

Full rules in `docs/git-hygiene.html`. You can be asked to carry out this plumbing directly.

| Kind           | Pattern                                                          |
| -------------- | ---------------------------------------------------------------- |
| Trunk          | `main`                                                           |
| Regular ticket | `developer/firstname.lastname/<ticket-id>-<ticket-title>`        |
| Large feature  | `feature/<feature-name>`, with developer branches merged into it |
| Release        | `release/x.y`                                                    |

**Rebase only**, both for syncing a branch and for merging a pull request. Rebase is the default
merge strategy on the remote; merge stays available for special cases, chiefly a large feature
branch whose history has become unmanageable. Never merge `main` into a branch — rebase onto it.

**Squash to one commit per ticket.** One PR, one ticket, one commit. The exception is when parts of
the change will need cherry-picking separately; keep those as their own commits.

**Release branches are live production.** Only minimal, low-risk changes are cherry-picked onto
them. Moving a site to a new version is a maintenance event, not a cherry-pick. Fixes land on
`main` first and are cherry-picked from there — never the reverse.

A hot fix to a released version gets a **clone ticket**, which cherry-picks the original commit and
records anything that went wrong during the pick, such as conflicts:

```
<Original Commit Message>

Cherry-picked from <commit-hash>

<Clone Ticket ID> <Clone Title>
```

Never `git push --force` a shared branch. Use `--force-with-lease`, and only on your own branch.

This guide describes what to do most of the time. Departing from it is sometimes correct — say why
in the pull request when you do.

---

## Code standards

**Python** — strict typing is mandatory and enforced in CI.

- `pyright --strict` must pass. No `# type: ignore` without a comment explaining why.
- No bare `Any`. No untyped function signatures.
- `ruff` for lint and format.
- Runtime validation at boundaries with pydantic; internal domain types are plain dataclasses.

**TypeScript** — `strict: true`, plus `noUncheckedIndexedAccess`.

- No `any`. Use `unknown` and narrow.
- No non-null assertions (`!`) without a comment justifying it.

**Generated code** (`**/gen/`) is never hand-edited and never committed. Regenerate with
`buf generate`.

### Naming

**Getters and setters are named `x()` / `set_x()`, in the file's own casing** — never
`get_x()`. Python: `version()` / `set_version()` (snake_case). TypeScript: `version()` /
`setVersion()` (camelCase). This applies to IPC methods bridged between processes as much as to
ordinary class methods — the bridged name is what callers actually see, so it follows the same
rule as any other getter.

### Comments

**Write a comment only when the code cannot explain itself.** Clear names, small functions and
obvious structure are the first tool; a comment is what is left over when those are not enough.

When one is needed:

- Keep it **brief, in plain English**. A sentence, not a paragraph.
- Explain **why**, not what. If a comment restates the line below it, delete it.
- Describe **what the code does now**. No cross-reference tags, no notes about planned work, no
  claims about systems that do not exist yet — those go stale silently and then mislead.
- Comments worth keeping usually record something surprising: a non-obvious constraint, a
  deliberate omission, or a trap the next reader would otherwise fall into.

Explanations of decisions belong in the commit message and its ticket, not in code.

---

## Toolchain

| Task                          | Command                                                               |
| ----------------------------- | ---------------------------------------------------------------------- |
| Python deps                   | `uv sync`                                                             |
| JS deps                       | `pnpm install`                                                        |
| Regenerate API types          | `buf generate`                                                        |
| Python types                  | `pyright`                                                             |
| TS types                      | `pnpm -r exec tsc --noEmit`                                           |
| Python tests                  | `pytest`                                                              |
| JS tests                      | `pnpm -r test`                                                        |
| Layer contracts               | `lint-imports`                                                        |
| Sync agent config             | `python scripts/sync_agent_config.py`                                 |
| Export AI audit log           | `python scripts/export_ai_audit.py`                                   |
| Read a decision               | Atlassian MCP server, configured in `.mcp.json`                       |
| Desktop Python deps           | `uv sync --project apps/desktop/backend`                              |
| Desktop JS deps                | `pnpm install` (in `apps/desktop/frontend`)                          |
| Generate proto code            | `python scripts/generate_proto.py <template> [--node-modules <dir>]` |
| Run desktop app (build mode)   | `python apps/desktop/dev_run.py`                                     |
| Run desktop app (hot reload)   | `python apps/desktop/dev_run.py --dev`                               |

Full environment setup is `/onboarding`.

> **If you change what a fresh clone needs, update `/onboarding` in the same change.**
>
> That skill is the only description of how to stand this project up, and a new engineer's first
> hour depends on it being true. It goes stale silently — nothing fails when it drifts, right up
> until someone joins and cannot start.
>
> Triggers: adding a dependency or a required CLI tool, adding or renaming a config file or
> environment variable, adding a backing service, changing a build or codegen step, changing how
> an app is started, or changing the test commands.
>
> The same applies to the commands in the table above and to `/review-branch` if the dependency
> layout changes.

---

## Plan mode and design decisions

**Larger design decisions are made in plan mode, through a questionnaire survey of the
options.** That covers architecture, a new dependency, a data model, a public interface, and
any cross-cutting refactor — anything that shapes the system rather than implementing it.

The shape of it:

1. Enumerate the realistic options. Two or three, not a survey of everything possible.
2. Give the trade-offs of each, including what each one costs.
3. **Ask the developer to choose, explicitly.** Do not infer a preference and proceed.
4. Build the chosen one. Record the decision in the ticket the work is committed under.

**A fresh session with significant scope starts in plan mode.** If the developer has not
enabled it, enable it rather than starting to implement. Judge by the work, not the wording of
the request: "add OAuth" is a design decision, "fix this typo" is not. When genuinely unsure,
plan mode costs one round trip and implementing the wrong design costs a session.

This exists because the developer must own the design and engineering decisions — see rule 4 of
`.integrity/POLICY.md`. It is not a limit on what you may build.

---

## Academic integrity

Full policy: **[`.integrity/POLICY.md`](.integrity/POLICY.md)** — required reading. The
statement format is `.integrity/AI-USE-STATEMENT.md`. In summary:

- **Disclose.** Any commit an agent helped produce carries an AI Use Statement naming the tool,
  model and mode. `README.md` and any substantial design document carry one too.
  Use `/commit-message`, which composes it.
- **Never write the `Verified:` field.** It is the developer's own account of how they checked
  the work. Ask, wait, and say the statement is not ready if they have not answered.
- **Do not add `Co-Authored-By` trailers.** The `commit-msg` hook rejects them. Disclosure of
  use is the statement; authorship stays with the human who is accountable.
- **Never paste sponsor or personal data into a prompt.** Describe the shape of data, not its
  contents. We use consumer tooling — assume prompts leave the building permanently.
- **A commit message is published.** Generalise sponsor, vendor and personal names in it. The
  audit log holds the full record; the public repository does not need it.
- **Third-party library source lives outside this repository.** Forks, open and closed source
  alike, belong in sibling directories and are never copied into this tree. Some are
  confidential — confirm with the developer before reading any of it.
- **Verify before you hand it over.** Check claims about libraries against their own
  documentation, and check that cited sources exist and say what you claimed.

---

## Working agreements for agents

- **Do not add a dependency** without stating what it is for, why the standard library or an
  existing dependency cannot do it, a link to its repository, and its maintenance signals.
  `connectrpc` is pinned to `0.4.*` deliberately. Do not upgrade it.
- **Build exactly what was asked.** Adjacent ideas go in a follow-ups list, not into the code.
- **Never guess file paths.** Search first, then read.
- Update `HANDOFF.md` (gitignored, dev-local) before ending a working session: current phase,
  what is stubbed, next actions, open questions.
- Stubs must carry a header comment naming what they are and what filling them in requires.
  A stub with no explanation is worse than no stub.
