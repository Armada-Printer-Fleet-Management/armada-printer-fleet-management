---
description: "Propose ways to split a finished branch into a stack of cohesive pull requests, recognising one ticket, one ticket needing several PRs, or several tickets in one branch, and let the developer choose. Read-only: returns the chosen plan. Use only when the work is done, as a step of /pr-precheck, never mid-work."
---
<!-- GENERATED FILE - DO NOT EDIT
     Source:    .claude/skills/pr-split/SKILL.md
     Generator: scripts/sync_agent_config.py -->

# PR split

Propose how a finished branch should become pull requests, and return the developer's choice as a
plan `/pr-precheck` can build. **This skill never runs a git command that writes.** It reads and
proposes.

**Only when the work is finished.** Reshaping branches mid-work causes more trouble than it saves,
so if the developer has not said the work is done, ask before going further.

## 1. Gather

Base is the argument, else `origin/main`.

```bash
git fetch origin
git merge-base HEAD origin/main
git log --format='%h %s%n%b%n---' <base>..HEAD
git diff --numstat <base>...HEAD
git diff --stat <base>...HEAD
```

Take each commit's ticket from its final line (`<TICKET-ID> <title>`) and the branch's from its
name (`[A-Z][A-Z0-9]{1,9}-[0-9]+`). Never invent a ticket ID.

## 2. Weigh the change by cohesion, not size

**There is no line limit.** A 2,000-line lockfile update is easy to review; 2,000 lines of core
logic are not. Weigh each changed file by how much a reviewer has to think:

| Weight | Files |
|---|---|
| Near zero | Lockfiles, generated code and generated docs (`docs/api/`, `.github/skills/`, `.github/prompts/`, `**/gen/`), formatting-only changes |
| Light | Docs, configuration, CI, skills |
| Heavy | `packages/proto/`, `packages/core-domain/`, domain services and repositories, infrastructure, plugins, UI logic |

Then group the files into **units**: changes that only make sense reviewed together. Follow the
layers in `ARCHITECTURE.md`: a contract change, the domain rules that use it, and the app wiring
are often three units, but one small feature through every layer is one unit.

**Split** when one PR would make a reviewer hold separate concerns at once (a contract redesign
plus new domain rules plus a UI flow), or when several tickets share a branch. **Do not split**
when a part cannot build, pass its tests, or make sense without the next part. A PR that cannot
stand alone is worse than a large one.

## 3. Recognise the case

| Case | What to propose |
|---|---|
| One ticket, cohesive | "No split" first: one PR, one commit |
| One ticket, several heavy units | One PR per unit, all carrying that ticket, named `<ticket-id>-<n>-<slug>` |
| Several tickets, separate commits | At least one PR per ticket, each keeping its own ticket and branch name |
| Several tickets mixed in one commit | Split by file per ticket. If one file holds work for two tickets, say so: hunk-level splits need the developer, because interactive git is not available to agents |

## 4. Order the stack

Each PR is based on the one before it (`main` for the first), so order by dependency:
`packages/proto` → `core-domain` → `plugin-api` → `plugins` → apps, with docs beside the code
they describe and tooling first if later PRs use it. Every PR must build on its base alone.

## 5. Offer two or three options

Always include the simplest reasonable option. For each option, list the ordered PRs, and for each PR:
its title, its ticket, its files (globs are fine), its weight, and one line on why it stands alone.

Ask with AskUserQuestion, one option per choice, with the stack drawn in the preview:

```text
main
 └─ PR 1  ARM-192  docs: split human pages from agent rules        light
     └─ PR 2  ARM-192  feat(skills): add PR stack precheck         light
         └─ PR 3  ARM-171  feat(hooks): gate pushes on DDD review   heavy
```

## 6. Return the plan

Return the chosen option as this block and nothing else, for `/pr-precheck` to build:

```text
PR SPLIT PLAN
base: <base ref>
1. branch: developer/<first.last>/<ticket-id>-<slug>
   ticket: <TICKET-ID> <ticket title>
   files: <path or glob>, ...
2. branch: ...
```

Every changed file appears in exactly one PR. Called directly by a developer, show the plan and
stop; building it is `/pr-precheck`'s job.
