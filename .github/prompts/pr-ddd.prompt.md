---
description: "Review the current branch's committed code changes for DDD and layering violations in a fresh agent context, score them, and record a verdict that the pre-push hook checks. Use before pushing any code change; /pr-precheck and /review-branch run it for you."
---
<!-- GENERATED FILE - DO NOT EDIT
     Source:    .claude/skills/pr-ddd/SKILL.md
     Generator: scripts/sync_agent_config.py -->

# PR DDD review

Review the committed changes on this branch against the project's architecture rules, and record
a verdict for the pre-push hook. You start with no conversation history: everything you need is
below and in the repository.

**Which checkout:** if this skill was given a path, it is the checkout to review (such as a
`/review-branch` worktree). Pass `--repo <path>` before the subcommand on every
`scripts/ddd_verdict.py` call below, and read files under that path. With no path, review the
current checkout.

**Preview mode:** if the arguments include `--preview`, the review covers uncommitted work in
progress. Add `--worktree` after `scope` and `diff`, ignore the uncommitted-edits stop in step 1,
and **skip step 5 entirely: a preview is never recorded**, so it cannot satisfy the push gate.
Report the findings and score as a preview.

**Spend as few tokens as the review allows.** Read the scoped diff, the rules named below, and a
full file only when a hunk cannot be judged without it. Do not explore the rest of the repository,
read tests, or run the test suite.

## 1. Scope

```bash
python scripts/ddd_verdict.py scope
```

It prints the merge base, HEAD's tree, every source file changed since the branch left `main`
(tests and generated code excluded), and any of those files with uncommitted edits. Every layer is
in scope on purpose: domain logic in the wrong place, such as a React component or a handler, is
the violation most worth catching.

- **No files:** report "nothing to review" and stop. The hook treats this as not applicable.
- **Uncommitted edits in scoped files:** report that the review covers commits only, name the
  files, and stop. A verdict is keyed to the committed tree, so reviewing a dirty tree would
  record the wrong thing.

## 2. Read the rules

Read only these, by section:

- Root `AGENTS.md`: _Architecture: ports and adapters_, _Domain-driven design_, _Open core_.
- The `AGENTS.md` of each app or package the scoped files sit in (`apps/server/`,
  `apps/desktop/`, `packages/proto/`), only the sections about layout, domains and adding a use case.
- `ARCHITECTURE.md`'s folder map, only when a file's layer is unclear from its path.

## 3. Read the diff

```bash
python scripts/ddd_verdict.py diff
```

## 4. Judge it

`lint-imports` already fails the build on import direction between layers, so do not spend effort
re-deriving it. Look for what a linter cannot see:

| Rule | A violation looks like |
|---|---|
| Domains couple by ID only | A domain's entity, service or port takes or returns another domain's entity type |
| Every entity ID is strongly typed | A bare `str`, `UUID` or `int` ID crossing a layer boundary |
| Entities hold the rules | A status check or transition decided in a service, handler, IPC module, repository or infrastructure class |
| Changes go through `change()` | A use case that loads, mutates and saves by hand, or saves after a refused rule |
| Services are the public interface | Code outside a domain calling its repository or reaching into an entity's internals |
| Clients never apply shared rules | Desktop code that saves a shared entity or applies its rule instead of `request_<action>()` |
| Handlers and infrastructure hold no rules | A Connect handler, router, IPC module or adapter deciding something the entity should |
| Proto messages are DTOs | Domain code importing generated proto types, or mapping done outside `proto_utils.mappers` |
| Plugins only through infrastructure | A service, handler or route importing a plugin or its port; an adapter constructed outside `apps/*` |
| Frontends have no domain layer | Business rules in `apps/web` or a desktop React component; web logic belongs on the server unless it is a performance optimisation |
| Desktop React goes through the backend | Desktop frontend code calling a server directly instead of over IPC |
| Logic is generic | An organisation, vendor or environment hardcoded in code instead of configuration |

Each finding has a severity:

- **violation**: the diff breaks one of the rules above, and you can point at the line. Any
  violation fails the push, so only use it when you are sure.
- **warning**: a likely problem, a smell, or a violation you are not sure about. Warnings never block.

Then score the change from 0 to 100 for how well it follows the architecture. Start at 100,
subtract 25 per violation and 5 per warning, and never go below 0. Give your confidence in the
review from 0 to 1, lower when the diff depends on code you did not read.

## 5. Record the verdict

Pipe exactly this JSON shape into the recorder. `line` may be `null`. The recorder derives pass or
fail from the severities, so do not include a verdict field.

```bash
python scripts/ddd_verdict.py record <<'EOF'
{
  "score": 85,
  "confidence": 0.8,
  "model": "<the model you are>",
  "findings": [
    {"rule": "Domains couple by ID only", "file": "path/to/file.py", "line": 42,
     "severity": "warning", "explanation": "One sentence a developer can act on."}
  ]
}
EOF
```

If it rejects the JSON, fix what it names and run it again.

## 6. Report

Return a short report: the recorded verdict and score, then each finding as
`path:line  severity  rule: explanation`. Say plainly if the verdict is a fail, and that a push
can override it with `ARMADA_DDD_OVERRIDE="<reason>" git push` when the review is wrong. Do not
modify any file other than through the recorder.
