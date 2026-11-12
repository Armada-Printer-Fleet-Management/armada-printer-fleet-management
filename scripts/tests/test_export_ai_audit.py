"""Tests for scripts/export_ai_audit.py: keeping excluded sessions out of the audit log.

Each test builds a throwaway repository and log folder. Standard library only, like the script:

    python -m unittest discover -s scripts/tests
"""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import export_ai_audit as audit

NORMAL_ID = "aaaaaaaa-1111-1111-1111-111111111111"
EXCLUDED_ID = "bbbbbbbb-2222-2222-2222-222222222222"
AUTHOR = "test.user"
REASON = "Used confidential beta material."


def claude_source(directory: Path) -> audit.Source:
    return audit.Source(
        tool="Claude Code",
        directory=directory,
        patterns=("*.jsonl",),
        structured=True,
        scoped_by_directory=True,
    )


def tool_call(name: str, tool_input: dict[str, str]) -> dict[str, object]:
    return {
        "type": "assistant",
        "timestamp": "2026-11-11T10:00:00Z",
        "message": {"model": "test-model", "content": [{"type": "tool_use", "name": name, "input": tool_input}]},
    }


def write_transcript(path: Path, session_id: str, records: list[dict[str, object]]) -> Path:
    lines = [{"sessionId": session_id, "timestamp": "2026-11-11T09:00:00Z", **record} for record in records]
    _ = path.write_text("\n".join(json.dumps(line) for line in lines) + "\n", encoding="utf-8")
    return path


class Workspace(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        base = Path(temporary.name)
        self.root = base / "repo"
        self.records = base / "records"
        self.log = base / "log"
        for directory in (self.root, self.records, self.log):
            directory.mkdir()
        self.config = audit.Config(log_dir=self.log, author=AUTHOR, extra_sources=())
        self.destination = self.log / audit.AUDIT_DIR_NAME / AUTHOR


class ExclusionListTest(Workspace):
    def test_missing_file_excludes_nothing(self) -> None:
        self.assertEqual(audit.read_exclusions(self.root), {})

    def test_comments_and_blank_lines_are_skipped(self) -> None:
        path = self.root / audit.EXCLUSIONS_FILE
        path.parent.mkdir(parents=True)
        _ = path.write_text(f"# a comment\n\n  {EXCLUDED_ID} {REASON}  \n\n# another\n", encoding="utf-8")

        self.assertEqual(audit.read_exclusions(self.root), {EXCLUDED_ID: REASON})

    def test_adding_twice_records_once(self) -> None:
        self.assertTrue(audit.add_exclusion(self.root, EXCLUDED_ID, REASON))
        self.assertFalse(audit.add_exclusion(self.root, EXCLUDED_ID, "A second reason."))

        self.assertEqual(audit.read_exclusions(self.root), {EXCLUDED_ID: REASON})

    def test_prefix_matches_full_session_id(self) -> None:
        excluded = audit.SessionFacts(session_id=EXCLUDED_ID, source=Path("x"), tool="Claude Code")
        normal = audit.SessionFacts(session_id=NORMAL_ID, source=Path("y"), tool="Claude Code")

        self.assertTrue(audit.is_listed(excluded, {EXCLUDED_ID[:8]: REASON}))
        self.assertFalse(audit.is_listed(normal, {EXCLUDED_ID[:8]: REASON}))


class ExportTest(Workspace):
    def setUp(self) -> None:
        super().setUp()
        source = claude_source(self.records)
        read = tool_call("Read", {"file_path": str(self.root / "src" / "main.py")})
        normal = write_transcript(self.records / f"{NORMAL_ID}.jsonl", NORMAL_ID, [read])
        excluded = write_transcript(self.records / f"{EXCLUDED_ID}.jsonl", EXCLUDED_ID, [read])
        patcher = mock.patch.object(audit, "find_records", return_value=[(source, normal), (source, excluded)])
        _ = patcher.start()
        self.addCleanup(patcher.stop)
        _ = audit.add_exclusion(self.root, EXCLUDED_ID[:8], REASON)

    def run_export(self, *, dry_run: bool = False, verified: str | None = None) -> None:
        with redirect_stdout(io.StringIO()):
            result = audit.export(
                self.root, self.config, dry_run=dry_run, quiet=True, only=None, verified=verified
            )
        self.assertEqual(result, 0)

    def folders(self) -> list[str]:
        return sorted(entry.name for entry in self.destination.iterdir() if entry.is_dir())

    def test_excluded_session_is_not_copied(self) -> None:
        self.run_export()

        self.assertEqual(self.folders(), ["2026-11-11_claude-code_aaaaaaaa"])
        self.assertTrue((self.destination / "2026-11-11_claude-code_aaaaaaaa" / "SESSION.md").is_file())

    def test_existing_copy_is_deleted_unless_dry_run(self) -> None:
        stale = self.destination / "2020-01-01_claude-code_bbbbbbbb"
        stale.mkdir(parents=True)
        _ = (stale / "SESSION.md").write_text("leaked", encoding="utf-8")

        self.run_export(dry_run=True)
        self.assertTrue(stale.is_dir())

        self.run_export()
        self.assertFalse(stale.exists())

    def test_verification_is_never_written_for_excluded_session(self) -> None:
        self.run_export(verified="Checked by hand.")

        normal = (self.destination / "2026-11-11_claude-code_aaaaaaaa" / "SESSION.md").read_text(encoding="utf-8")
        self.assertIn("Checked by hand.", normal)
        self.assertEqual(list(self.destination.glob("*_bbbbbbbb")), [])

    def test_index_lists_excluded_session_without_a_link(self) -> None:
        self.run_export()

        index = (self.destination / "INDEX.md").read_text(encoding="utf-8")
        self.assertIn("1 session(s) exported, 1 excluded.", index)
        rows = [line for line in index.splitlines() if "bbbbbbbb" in line]
        self.assertEqual(len(rows), 1)
        self.assertIn(audit.EXCLUDED_STATUS, rows[0])
        self.assertNotIn("](", rows[0])
        self.assertNotIn(REASON, index)


if __name__ == "__main__":
    _ = unittest.main()
