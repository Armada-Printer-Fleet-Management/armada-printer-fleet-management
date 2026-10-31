"""Scope, record and check the /pr-ddd architecture review of the current commit.

The review itself is an agent's judgement; everything around it is deterministic so the
pre-push hook can rely on it without spending tokens:

    scope    the source files changed since the branch left main, as JSON
    diff     the unified diff of only those files, which is all the reviewer reads
             (both take --worktree to preview uncommitted work, which is never recorded)
    record   validate a review on stdin and store it as the verdict for HEAD's tree
    check    exit 0 if HEAD needs no review, has a passing verdict, or is overridden
    inherit  give HEAD a reviewed tree's passing verdict, for a PR stack split from that tree
    show     print the stored verdict for HEAD's tree

Verdicts live under the git common directory, so every worktree of a clone shares them,
and are keyed by tree hash: rewording or re-squashing a commit keeps its verdict, while
any change to the code needs a new one.

The verdict is derived here from the findings, never taken from the reviewer: any finding
of severity "violation" fails. A failure is overridden for one push with
ARMADA_DDD_OVERRIDE="<reason>", which is recorded beside the verdict.

Standard library only, by design: this runs from git hooks before dependencies exist.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

# Every layer is in scope: the violation to catch is often domain logic in the wrong place.
SCOPED_SUFFIXES = (".py", ".ts", ".tsx", ".proto")
# Tests and generated code follow from the code under review; reading them only costs tokens.
SKIPPED_PARTS = {
    "tests",
    "test",
    "__tests__",
    "e2e",
    "gen",
    "_gen",
    "migrations",
    "node_modules",
}
SKIPPED_NAME_ENDINGS = (
    ".test.ts",
    ".test.tsx",
    ".spec.ts",
    ".spec.tsx",
    "_test.py",
    ".d.ts",
)

SEVERITIES = {"violation", "warning"}
OVERRIDE_ENV = "ARMADA_DDD_OVERRIDE"


class InvalidReview(ValueError):
    """The reviewer's JSON does not match the verdict contract."""


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], check=True, capture_output=True, text=True, encoding="utf-8"
    ).stdout.strip()


def merge_base() -> str:
    for ref in ("origin/main", "main"):
        try:
            return git("merge-base", "HEAD", ref)
        except subprocess.CalledProcessError:
            continue
    raise SystemExit("Cannot find main or origin/main to compare against.")


def head_tree() -> str:
    return git("rev-parse", "HEAD^{tree}")


def is_scoped(path: str) -> bool:
    name = Path(path).name
    if not path.endswith(SCOPED_SUFFIXES) or name.endswith(SKIPPED_NAME_ENDINGS):
        return False
    if name.startswith("test_"):
        return False
    return not any(part in SKIPPED_PARTS for part in Path(path).parts)


def scoped_files(base: str) -> list[str]:
    changed = git(
        "diff", "--name-only", "--diff-filter=ACMR", base, "HEAD"
    ).splitlines()
    return [path for path in changed if is_scoped(path)]


def worktree_files(base: str) -> tuple[list[str], list[str]]:
    """Scoped files differing from the base in the working tree: (tracked, untracked)."""
    tracked = git("diff", "--name-only", "--diff-filter=ACMR", base).splitlines()
    untracked = git("ls-files", "--others", "--exclude-standard").splitlines()
    return (
        [path for path in tracked if is_scoped(path)],
        [path for path in untracked if is_scoped(path)],
    )


def verdict_dir() -> Path:
    common = Path(git("rev-parse", "--git-common-dir"))
    if not common.is_absolute():
        common = Path(git("rev-parse", "--show-toplevel")) / common
    return common / "armada" / "pr-ddd"


def verdict_path(tree: str) -> Path:
    return verdict_dir() / f"{tree}.json"


def validate_findings(raw: object) -> list[dict[str, object]]:
    if not isinstance(raw, list):
        raise InvalidReview("findings must be a list")
    findings: list[dict[str, object]] = []
    for index, item in enumerate(cast(list[object], raw)):
        if not isinstance(item, dict):
            raise InvalidReview(f"findings[{index}] must be an object")
        finding = cast(dict[str, object], item)
        for key in ("rule", "file", "explanation"):
            if not isinstance(finding.get(key), str) or not finding[key]:
                raise InvalidReview(
                    f"findings[{index}].{key} must be a non-empty string"
                )
        if finding.get("severity") not in SEVERITIES:
            raise InvalidReview(
                f"findings[{index}].severity must be one of {sorted(SEVERITIES)}"
            )
        line = finding.get("line")
        if line is not None and (not isinstance(line, int) or isinstance(line, bool)):
            raise InvalidReview(f"findings[{index}].line must be an integer or null")
        findings.append(finding)
    return findings


def validate_review(raw: object) -> dict[str, object]:
    """Check a reviewer's JSON and derive the verdict from its findings."""
    if not isinstance(raw, dict):
        raise InvalidReview("the review must be a JSON object")
    review = cast(dict[str, object], raw)

    score = review.get("score")
    if not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 100:
        raise InvalidReview("score must be an integer from 0 to 100")
    confidence = review.get("confidence")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        raise InvalidReview("confidence must be a number from 0 to 1")
    if not 0 <= confidence <= 1:
        raise InvalidReview("confidence must be a number from 0 to 1")
    model = review.get("model")
    if not isinstance(model, str) or not model:
        raise InvalidReview("model must name the reviewing model")

    findings = validate_findings(review.get("findings"))
    failed = any(finding["severity"] == "violation" for finding in findings)
    return {
        "verdict": "fail" if failed else "pass",
        "score": score,
        "confidence": float(confidence),
        "model": model,
        "findings": findings,
    }


def load_verdict(tree: str) -> dict[str, object] | None:
    path = verdict_path(tree)
    if not path.is_file():
        return None
    return cast(dict[str, object], json.loads(path.read_text(encoding="utf-8")))


def command_scope(args: argparse.Namespace) -> int:
    base = merge_base()
    if args.worktree:
        tracked, untracked = worktree_files(base)
        preview = {"base": base, "preview": True, "files": tracked + untracked}
        print(json.dumps(preview, indent=2))
        return 0
    files = scoped_files(base)
    edited = git("diff", "--name-only", "HEAD").splitlines()
    untracked = git("ls-files", "--others", "--exclude-standard").splitlines()
    dirty = [path for path in edited + untracked if is_scoped(path)]
    print(
        json.dumps(
            {"base": base, "tree": head_tree(), "files": files, "uncommitted": dirty},
            indent=2,
        )
    )
    return 0


def command_diff(args: argparse.Namespace) -> int:
    base = merge_base()
    if args.worktree:
        tracked, untracked = worktree_files(base)
        if tracked:
            print(git("diff", "--unified=3", base, "--", *tracked))
        for path in untracked:
            print(f"=== new file, not yet tracked: {path}")
            print(Path(path).read_text(encoding="utf-8"))
        return 0
    files = scoped_files(base)
    if files:
        print(git("diff", "--unified=3", base, "HEAD", "--", *files))
    return 0


def command_record(_: argparse.Namespace) -> int:
    try:
        review = validate_review(json.loads(sys.stdin.read()))
    except (InvalidReview, json.JSONDecodeError) as error:
        print(f"Review rejected: {error}", file=sys.stderr)
        return 2

    tree = head_tree()
    review["tree"] = tree
    review["base"] = merge_base()
    review["recorded_at"] = datetime.now(UTC).isoformat(timespec="seconds")

    path = verdict_path(tree)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")
    print(
        f"{review['verdict']} (score {review['score']}) recorded for tree {tree[:12]}"
    )
    return 0


def command_check(_: argparse.Namespace) -> int:
    if not scoped_files(merge_base()):
        print("not applicable: no source code changes")
        return 0

    tree = head_tree()
    verdict = load_verdict(tree)
    if verdict is not None and verdict.get("verdict") == "pass":
        print(f"pass, score {verdict.get('score')}, for tree {tree[:12]}")
        return 0

    reason = os.environ.get(OVERRIDE_ENV, "").strip()
    if reason:
        record = {
            "tree": tree,
            "reason": reason,
            "verdict": verdict and verdict.get("verdict"),
        }
        path = verdict_dir() / f"{tree}.override.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        print(f"OVERRIDDEN: {reason}")
        print("Put this reason in the pull request description.")
        return 0

    if verdict is None:
        print(f"No /pr-ddd review for this commit (tree {tree[:12]}).")
        print("Run /pr-ddd, or /pr-precheck which runs it.")
    else:
        violations = [
            finding
            for finding in cast(list[dict[str, object]], verdict.get("findings", []))
            if finding.get("severity") == "violation"
        ]
        print(f"/pr-ddd found {len(violations)} violation(s):")
        for finding in violations:
            location = f"{finding.get('file')}:{finding.get('line') or ''}".rstrip(":")
            print(f"  {location}  {finding.get('rule')}: {finding.get('explanation')}")
    print(f'To push anyway: {OVERRIDE_ENV}="<why the review is wrong>" git push')
    return 1


def command_inherit(args: argparse.Namespace) -> int:
    source = load_verdict(args.tree)
    if source is None or source.get("verdict") != "pass":
        print(
            f"Tree {args.tree[:12]} has no passing verdict to inherit.", file=sys.stderr
        )
        return 1
    reviewed = cast(str, source.get("base"))
    if git("merge-base", "HEAD", reviewed) != reviewed:
        print(
            "HEAD does not build on the reviewed base; run /pr-ddd instead.",
            file=sys.stderr,
        )
        return 1

    tree = head_tree()
    inherited = {**source, "tree": tree, "inherited_from": args.tree}
    inherited["recorded_at"] = datetime.now(UTC).isoformat(timespec="seconds")
    verdict_path(tree).write_text(
        json.dumps(inherited, indent=2) + "\n", encoding="utf-8"
    )
    print(f"pass inherited from tree {args.tree[:12]} for tree {tree[:12]}")
    return 0


def command_show(_: argparse.Namespace) -> int:
    verdict = load_verdict(head_tree())
    if verdict is None:
        print("No verdict recorded for this commit.")
        return 1
    print(json.dumps(verdict, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scope, record and check /pr-ddd verdicts."
    )
    parser.add_argument(
        "--repo",
        type=Path,
        help="checkout to work on, such as a /review-branch worktree; defaults to the current one",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    for name, handler in (
        ("scope", command_scope),
        ("diff", command_diff),
        ("record", command_record),
        ("check", command_check),
        ("show", command_show),
    ):
        command = commands.add_parser(name)
        command.set_defaults(handler=handler)
        if name in ("scope", "diff"):
            command.add_argument(
                "--worktree",
                action="store_true",
                help="preview uncommitted work; a preview is never recorded as a verdict",
            )
    inherit = commands.add_parser("inherit")
    inherit.add_argument(
        "tree", help="the reviewed tree whose passing verdict the split stack shares"
    )
    inherit.set_defaults(handler=command_inherit)
    args = parser.parse_args(argv)
    if args.repo is not None:
        os.chdir(args.repo)
    return cast(int, args.handler(args))


if __name__ == "__main__":
    sys.exit(main())
