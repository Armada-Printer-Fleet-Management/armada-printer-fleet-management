"""Lists the projects a push affects, so the pre-push hook checks only those.

    changed files (base...HEAD, plus uncommitted and untracked)
        │
        ├─ any global file? ──────────────────────────────► ALL
        │
        ▼
    projects that contain a changed file
        │  + packages/proto/ changed → projects owning a buf.gen.*.yaml `out:`
        ▼
    + every project that depends on one of them, transitively
      (pyproject [tool.uv.sources] paths, package.json workspace: deps)
        │
        ▼
    one repo-relative project directory per line

A project is any directory with a pyproject.toml or package.json. The base is
PRE_PUSH_BASE, else origin/main. PRE_PUSH_ALL=1, or any error, prints ALL: the hook
checks more, never less.

Standard library only, by design: this runs from git hooks before dependencies exist.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tomllib
from collections.abc import Iterable
from pathlib import Path

ALL = "ALL"
PROTO_DIR = "packages/proto/"
MANIFESTS = ("pyproject.toml", "package.json")
SKIPPED_DIRS = {"node_modules", ".venv", ".git", "dist", "build"}

# Files every check depends on: a change here re-checks the whole repository.
GLOBAL_PREFIXES = (".githooks/",)
GLOBAL_FILES = {
    "scripts/affected_projects.py",
    "scripts/generate_proto.py",
    "buf.yaml",
    "buf.lock",
    "package.json",
    "pnpm-lock.yaml",
    "pnpm-workspace.yaml",
}
GLOBAL_PATTERNS = (
    re.compile(r"^buf\.gen\.[^/]+\.yaml$"),
    re.compile(r"^(eslint|prettier)\.config\.[^/]+$"),
    re.compile(r"^tsconfig[^/]*\.json$"),
)

_OUT = re.compile(r"^\s*out:\s*(\S+)", re.MULTILINE)


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout


def base_ref(root: Path) -> str:
    override = os.environ.get("PRE_PUSH_BASE")
    if override:
        return override
    for ref in ("origin/main", "main"):
        if (
            subprocess.run(
                ["git", "rev-parse", "--verify", "--quiet", ref],
                cwd=root,
                capture_output=True,
                check=False,
            ).returncode
            == 0
        ):
            return ref
    raise RuntimeError("Cannot find origin/main or main to compare against.")


def changed_files(root: Path, base: str) -> set[str]:
    committed = git(root, "diff", "--name-only", f"{base}...HEAD")
    uncommitted = git(root, "diff", "--name-only", "HEAD")
    untracked = git(root, "ls-files", "--others", "--exclude-standard")
    return {
        line
        for text in (committed, uncommitted, untracked)
        for line in text.splitlines()
        if line
    }


def is_global(path: str) -> bool:
    return (
        path.startswith(GLOBAL_PREFIXES)
        or path in GLOBAL_FILES
        or any(pattern.match(path) for pattern in GLOBAL_PATTERNS)
    )


def find_projects(root: Path) -> list[str]:
    projects: list[str] = []
    for directory, subdirs, files in os.walk(root):
        rel = Path(directory).relative_to(root).as_posix()
        # Dot directories hold tooling and nested worktrees (.claude/worktrees), never projects.
        subdirs[:] = [
            d for d in subdirs if d not in SKIPPED_DIRS and not d.startswith(".")
        ]
        if rel != "." and any(manifest in files for manifest in MANIFESTS):
            projects.append(rel)
    return projects


def owner(path: str, projects: Iterable[str]) -> str | None:
    """The innermost project containing a path."""
    matches = [p for p in projects if path == p or path.startswith(f"{p}/")]
    return max(matches, key=len, default=None)


def dependencies(root: Path, project: str, by_name: dict[str, str]) -> set[str]:
    """The local projects a project depends on, from its manifests."""
    found: set[str] = set()
    pyproject = root / project / "pyproject.toml"
    if pyproject.is_file():
        sources = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        for source in sources.get("tool", {}).get("uv", {}).get("sources", {}).values():
            if isinstance(source, dict) and "path" in source:
                found.add((Path(project) / str(source["path"])).as_posix())
    package = root / project / "package.json"
    if package.is_file():
        manifest = json.loads(package.read_text(encoding="utf-8"))
        for field in ("dependencies", "devDependencies", "peerDependencies"):
            for name, spec in manifest.get(field, {}).items():
                if str(spec).startswith("workspace:") and name in by_name:
                    found.add(by_name[name])
    return {os.path.normpath(p).replace(os.sep, "/") for p in found}


def package_names(root: Path, projects: Iterable[str]) -> dict[str, str]:
    names: dict[str, str] = {}
    for project in projects:
        package = root / project / "package.json"
        if package.is_file():
            name = json.loads(package.read_text(encoding="utf-8")).get("name")
            if isinstance(name, str):
                names[name] = project
    return names


def proto_consumers(root: Path, projects: Iterable[str]) -> set[str]:
    """Projects that own generated code, from every buf.gen template's `out:` paths."""
    consumers: set[str] = set()
    for template in root.glob("buf.gen.*.yaml"):
        for out in _OUT.findall(template.read_text(encoding="utf-8")):
            project = owner(out, projects)
            if project:
                consumers.add(project)
    return consumers


def affected(root: Path, changed: set[str]) -> list[str] | None:
    """The affected project directories, or None when everything is."""
    if any(is_global(path) for path in changed):
        return None
    projects = find_projects(root)
    by_name = package_names(root, projects)

    dependents: dict[str, set[str]] = {p: set() for p in projects}
    for project in projects:
        for dependency in dependencies(root, project, by_name):
            dependents.setdefault(dependency, set()).add(project)

    hit = {p for p in (owner(path, projects) for path in changed) if p}
    if any(path.startswith(PROTO_DIR) for path in changed):
        hit |= proto_consumers(root, projects)

    pending = list(hit)
    while pending:
        for dependent in dependents.get(pending.pop(), set()):
            if dependent not in hit:
                hit.add(dependent)
                pending.append(dependent)
    return sorted(hit)


def main() -> int:
    if os.environ.get("PRE_PUSH_ALL") == "1":
        print(ALL)
        return 0
    try:
        root = Path(git(Path.cwd(), "rev-parse", "--show-toplevel").strip())
        base = base_ref(root)
        print(f"base: {base}", file=sys.stderr)
        result = affected(root, changed_files(root, base))
    except Exception as error:  # noqa: BLE001 -- any failure must widen the checks, never stop them.
        print(
            f"cannot scope the checks ({error}); checking everything", file=sys.stderr
        )
        result = None
    print(ALL if result is None else "\n".join(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
