---
name: pr-precheck
description: "Take finished work to open pull requests: run every pre-push check, the /pr-ddd architecture review, and /pr-split to choose a PR stack, then build one squashed commit per PR with /commit-message, push, and open each PR with a diagram. Use when the work is done and ready to push, never mid-work."
argument-hint: "[base-branch]"
---

# PR precheck

The pre-push routine for finished work. It ends with pull requests open and ready for reviewers.
**Run it only when the work is done**: reshaping branches mid-work causes more trouble than it
saves. If the developer has not said the work is finished, ask.

Every push and every `gh pr create` is approved by the developer as it happens. Never
`--force` a branch; `--force-with-lease` only, and only on the developer's own branches.

## 0. Prepare

1. `git status --short` must be clean. If it is not, show what is uncommitted and ask whether to
   commit it first, leave it out, or stop.
2. Base is the argument, else `origin/main`. Run `git fetch origin`. If the branch is behind the
   base, ask to rebase onto it (`git rebase origin/main`); never merge `main` in.
3. Keep a backup of the starting point: `git branch <branch>-precheck-backup HEAD`. Tell the
   developer its name; they delete it once the PRs are merged.

Record `ORIG` (the commit) and `ORIG_TREE` (`git rev-parse HEAD^{tree}`).

## 1. Architecture review

Run `/pr-ddd`. It reviews the changed source code and records a verdict for `ORIG_TREE`.

- **pass** or **nothing to review**: continue.
- **fail**: show the findings. The developer chooses: fix them (stop here; run `/pr-precheck`
  again after), or give a reason the review is wrong. Keep that reason: it goes into the PR
  description, and pushes use `ARMADA_DDD_OVERRIDE="<reason>"`.

## 2. Every other check

```bash
python scripts/sync_agent_config.py --check
bash .githooks/pre-push
```

`.githooks/pre-push` runs exactly what a push will run, including the DDD gate. Fix failures
before going on; do not push past them. If the developer overrode the review in step 1, run it as
`ARMADA_DDD_OVERRIDE="<reason>" bash .githooks/pre-push`.

## 3. Choose the stack

Run `/pr-split` and take the plan it returns. A one-PR plan is the common case.

## 4. Build the branches

For each PR in the plan, in order, with `BASE` being the base for PR 1 and the previous PR's
branch after that:

```bash
git switch -c <branch> <BASE>
git checkout <ORIG> -- <files this PR adds or changes>
git rm -q <files this PR deletes>
```

When a planned branch has the current branch's name, use `git switch -C <branch> <BASE>`
instead, which resets it to `BASE`. The backup from step 0 still holds the original work.

Then compose its message with `/commit-message <TICKET-ID> <ticket title>`, which asks the
developer for `Verified:`. **Never write `Verified:` yourself; without the developer's answer the
commit is not ready.** Commit it, one commit per PR, then give the branch its verdict (below)
before building the next.

After the last PR, `git diff <ORIG> HEAD` must be empty: the stack holds exactly the original work.
If it is not, stop and show the difference.

If the plan needs part of one file in one PR and the rest in another, stop and ask the developer
to make that split by hand. Interactive git is not available to agents.

**Verdicts for the stack.** Each branch has a new tree, so it has no verdict of its own yet. When
`/pr-ddd` passed `ORIG_TREE`, give each branch that verdict instead of paying for another review:

```bash
python scripts/ddd_verdict.py inherit <ORIG_TREE>
```

When the review failed and the developer overrode it, every push in the stack uses the override.

## 5. Describe each PR

Write each PR body to a file, in this shape:

```markdown
## What and why
<two to four plain sentences>

## Architecture review
/pr-ddd: <pass | fail, overridden: reason | not applicable>, score <n>.

<TICKET-ID> <ticket title>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

**Diagram.** The PR Lens GitHub App comments a diagram on every PR by itself. Ask the developer
once per run whether to also attach a local PR Lens diagram. Do this when the App is not installed,
or has stopped working, or before the PR exists. It spends the developer's own agent usage, about
12 to 18 thousand tokens per PR when kept lean, and nothing is billed to anyone else. If yes:

```bash
npx @coldtea/pr-lens-cli@0.14.0 skill
```

Keep it lean:

- Read that output once per run, not once per PR. Where it says `@latest`, use the pinned version.
- Do not load `skill references` (about 11 thousand more tokens). `validate` names the exact field
  that is wrong; read the references only if the same document fails validation twice.
- Write the graph document from the diff you already read for the review. Do not re-read files.
- Draw one architecture view, plus a data flow only when the change has a sequence a reviewer must
  follow. Attach the light theme only.

The output has you write a graph document, validate it, and render SVGs, which
`gh pr create --attach` adds to the description. `--attach` needs GitHub CLI 2.99 or newer
(`gh --version`). Fix names in `.github/pr-lens.yml`, never in the SVGs. Write the graph document
yourself and use only `skill`, `validate` and `render`: never `analyze`, which needs a paid model
key, or `canvas`, which uploads to prlens.dev.

## 6. Push and open

For each PR in order, after the developer approves:

```bash
git push -u origin <branch> --force-with-lease
gh pr create --base <BASE> --head <branch> --title "<commit subject>" --body-file <body file> [--attach <svg>...]
```

**Make it a GitHub stack.** With two or more PRs, link them, bottom to top, into a native stacked
pull request with the official `gh stack` extension:

```bash
gh stack link <PR 1 number> <PR 2 number> ...
```

GitHub then shows each PR's place in the stack (`1/3`, `2/3`, ...) and a stack page; it prints the
stack number. Do not write positions or neighbour links into titles or bodies: the stack shows
them. `link` keeps the PRs and corrects any base that breaks the chain.

Prefix the push with `ARMADA_DDD_OVERRIDE="<reason>"` only when the developer gave an override
reason in step 1. Report each PR's URL. The developer adds the reviewers.

## 7. Hand over

Give the developer the stack page link, `https://github.com/<owner>/<repo>/stack/<number>`, and
tell them how it merges: from the stack page, or with `gh stack merge <stack number>`. GitHub's
stack merge is atomic: it merges every PR up to the one chosen, in one operation, and either all
of them land or none do. Branch protection still applies to each.

Then switch back to the developer's original branch, and remind them that
`<branch>-precheck-backup` can be deleted once everything is merged.
