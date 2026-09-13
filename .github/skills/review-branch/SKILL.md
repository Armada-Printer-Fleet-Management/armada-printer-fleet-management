---
name: review-branch
description: "Check out a colleague's branch in a git worktree beside the repo, reusing the main checkout's installed dependencies when lockfiles match, then summarise the change for review. Use when reviewing someone else's branch or PR locally."
---
<!-- GENERATED FILE - DO NOT EDIT
     Source:    .claude/skills/review-branch/SKILL.md
     Generator: scripts/sync_agent_config.py -->

# Review branch

Set up a colleague's branch in an isolated worktree without disturbing the current checkout, then
help review it.

Reinstalling dependencies per worktree is the slow part, so when lockfiles are unchanged the
worktree points at the main checkout's already-installed dependencies instead of duplicating them.

## Input

`/review-branch <branch-name>`

If no branch is given, list recent remote branches (`git branch -r --sort=-committerdate | head -20`)
and ask which one.

## Steps

**1. Locate the main worktree.** The first entry of `git worktree list` is the main checkout.
Everything below resolves against it — do not assume the current directory is it, since this skill
may run from inside another worktree.

**2. Fetch the branch.**

```
git fetch origin <branch>
```

**3. Create the worktree** as a sibling of the repository, so worktree files never appear inside
the repo's own tree:

```
git worktree add "../<repo-name>-worktrees/<branch-slug>" "origin/<branch>"
```

Replace `/` and other path-unsafe characters in the branch name with `-` for the directory name.
If the worktree already exists, reuse it: `git -C <path> fetch && git -C <path> reset --hard origin/<branch>`.

**4. Decide per ecosystem whether dependencies can be shared.**

Compare each lockfile between the main checkout and the worktree:

| Ecosystem | Lockfile | Shared directory |
|---|---|---|
| Node | `pnpm-lock.yaml` | `node_modules` |
| Python | `uv.lock` | `.venv` |

For each: if the lockfile is byte-identical and the main checkout's directory exists, link it.
Otherwise run the real install in the worktree (`pnpm install` / `uv sync`).

Compare with `git diff --no-index --quiet <main>/<lockfile> <worktree>/<lockfile>`, or hash both.

**5. Link when shared.**

Windows (junctions need no administrator rights):

```powershell
New-Item -ItemType Junction -Path "<worktree>\node_modules" -Target "<main>\node_modules"
New-Item -ItemType Junction -Path "<worktree>\.venv"        -Target "<main>\.venv"
```

Linux and macOS:

```bash
ln -s "<main>/node_modules" "<worktree>/node_modules"
ln -s "<main>/.venv"        "<worktree>/.venv"
```

Never create the link over an existing real directory — check first and skip if one is present.

**6. Report what happened**, per ecosystem: linked, or installed and why. The user needs to know
whether they are testing against shared or fresh dependencies.

**7. Summarise the change for review.**

```
git -C <worktree> diff --stat main...origin/<branch>
git -C <worktree> log --oneline main..origin/<branch>
git -C <worktree> diff main...origin/<branch>
```

Use `main...origin/<branch>` (three dots) so the diff is against the merge base rather than
whatever `main` currently points at.

Then give a short review: what the change does, anything that looks incorrect, and anything that
contradicts the conventions in `CLAUDE.md`. Point at files by path and line.

## Caveats to tell the user

- A linked `.venv` is shared, not copied. Installing a package inside the worktree modifies the
  main checkout's environment too. If they need to install anything, unlink first and run a real
  `uv sync`. The same applies to `node_modules`.
- Lockfiles matching does not guarantee the branch needs nothing new — a dependency added without
  the lockfile being regenerated will appear to match. If an import fails at runtime, that is the
  likely cause; fall back to a real install.

## Cleanup

```
git worktree remove "../<repo-name>-worktrees/<branch-slug>"
git worktree prune
```

Remove the junction or symlink before removing the worktree, so the removal cannot follow the link
into the main checkout's dependencies. On Windows: `(Get-Item <path>).Delete()`. On Linux and
macOS: `rm` the link itself, never `rm -r` through it.
