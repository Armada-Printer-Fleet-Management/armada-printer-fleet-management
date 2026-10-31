"""Tests for scripts/ddd_verdict.py: the push gate's check and the PR stack's inherit.

Each test builds a throwaway repository, because the script's behaviour is defined by git state.
Standard library only, like the script, so they run before any dependency is installed:

    python -m unittest discover -s scripts/tests
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import ddd_verdict

GIT_IDENTITY = {
    "GIT_AUTHOR_NAME": "test",
    "GIT_AUTHOR_EMAIL": "test@example.invalid",
    "GIT_COMMITTER_NAME": "test",
    "GIT_COMMITTER_EMAIL": "test@example.invalid",
}

PASSING_REVIEW = {"score": 95, "confidence": 0.9, "model": "test", "findings": []}
FAILING_REVIEW = {
    "score": 75,
    "confidence": 0.9,
    "model": "test",
    "findings": [
        {
            "rule": "Domains couple by ID only",
            "file": "apps/server/api/domains/job.py",
            "line": 1,
            "severity": "violation",
            "explanation": "Imports another domain's entity.",
        }
    ],
}


class RepoTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.cwd = Path.cwd()
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        self.env = mock.patch.dict(os.environ, GIT_IDENTITY)
        self.env.start()
        os.environ.pop(ddd_verdict.OVERRIDE_ENV, None)
        self.git("init", "-q", "-b", "main")
        self.commit({"README.md": "start\n"}, "start")

    def tearDown(self) -> None:
        os.chdir(self.cwd)
        self.env.stop()
        self.temp.cleanup()

    def git(self, *args: str) -> str:
        return subprocess.run(
            ["git", *args], cwd=self.repo, check=True, capture_output=True, text=True
        ).stdout.strip()

    def commit(self, files: dict[str, str], message: str) -> None:
        for name, content in files.items():
            path = self.repo / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)

    def tree(self) -> str:
        return self.git("rev-parse", "HEAD^{tree}")

    def run_script(self, *args: str, stdin: str = "") -> tuple[int, str]:
        out, err = io.StringIO(), io.StringIO()
        with (
            mock.patch("sys.stdin", io.StringIO(stdin)),
            redirect_stdout(out),
            redirect_stderr(err),
        ):
            code = ddd_verdict.main(["--repo", str(self.repo), *args])
        os.chdir(self.cwd)
        return code, out.getvalue() + err.getvalue()

    def record(self, review: dict[str, object]) -> None:
        code, output = self.run_script("record", stdin=json.dumps(review))
        self.assertEqual(code, 0, output)


class CheckTests(RepoTestCase):
    def test_not_applicable_without_source_changes(self) -> None:
        self.git("switch", "-q", "-c", "work")
        self.commit({"docs/guide.md": "words\n"}, "docs only")

        code, output = self.run_script("check")

        self.assertEqual(code, 0)
        self.assertIn("not applicable", output)

    def test_passes_with_a_pass_verdict_for_head_tree(self) -> None:
        self.git("switch", "-q", "-c", "work")
        self.commit({"apps/server/api/domains/job.py": "x = 1\n"}, "code")
        self.record(PASSING_REVIEW)

        code, output = self.run_script("check")

        self.assertEqual(code, 0)
        self.assertIn("pass", output)


class InheritTests(RepoTestCase):
    def reviewed_branch(self, review: dict[str, object]) -> str:
        """A two-file change on `work`, reviewed; returns its tree."""
        self.git("switch", "-q", "-c", "work")
        self.commit(
            {
                "packages/core-domain/job.py": "rule = 1\n",
                "apps/server/api/domains/job.py": "use = 1\n",
            },
            "full change",
        )
        self.record(review)
        return self.tree()

    def split_branch(self, start: str) -> None:
        """The first PR of a stack: part of the reviewed change, built from `start`."""
        self.git("switch", "-q", "-c", "split", start)
        self.git("checkout", "work", "--", "packages/core-domain/job.py")
        self.git("commit", "-q", "-m", "first part")

    def test_split_branch_inherits_a_pass_and_then_passes_check(self) -> None:
        reviewed = self.reviewed_branch(PASSING_REVIEW)
        self.split_branch("main")

        code, output = self.run_script("inherit", reviewed)
        self.assertEqual(code, 0, output)

        stored = json.loads(ddd_verdict_path(self.repo, self.tree()).read_text("utf-8"))
        self.assertEqual(stored["verdict"], "pass")
        self.assertEqual(stored["inherited_from"], reviewed)
        self.assertEqual(self.run_script("check")[0], 0)

    def test_refuses_a_tree_with_no_verdict(self) -> None:
        self.git("switch", "-q", "-c", "work")
        self.commit({"apps/server/api/domains/job.py": "x = 1\n"}, "unreviewed")

        code, output = self.run_script("inherit", self.tree())

        self.assertEqual(code, 1)
        self.assertIn("no passing verdict", output)

    def test_refuses_a_failing_verdict(self) -> None:
        reviewed = self.reviewed_branch(FAILING_REVIEW)
        self.split_branch("main")

        code, output = self.run_script("inherit", reviewed)

        self.assertEqual(code, 1)
        self.assertIn("no passing verdict", output)
        self.assertFalse(ddd_verdict_path(self.repo, self.tree()).exists())

    def test_refuses_a_branch_that_does_not_build_on_the_reviewed_base(self) -> None:
        first = self.git("rev-parse", "HEAD")
        self.commit({"README.md": "moved on\n"}, "main moves")
        reviewed = self.reviewed_branch(PASSING_REVIEW)
        self.split_branch(first)

        code, output = self.run_script("inherit", reviewed)

        self.assertEqual(code, 1)
        self.assertIn("does not build on the reviewed base", output)


def ddd_verdict_path(repo: Path, tree: str) -> Path:
    return repo / ".git" / "armada" / "pr-ddd" / f"{tree}.json"


if __name__ == "__main__":
    unittest.main()
