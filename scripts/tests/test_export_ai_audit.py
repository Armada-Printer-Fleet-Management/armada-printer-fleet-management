"""Tests for Copilot and Claude Code source discovery in the audit exporter."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import export_ai_audit


class FindRecordsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.root = self.base / "Armada"
        self.root.mkdir()
        self.home = self.base / "home"
        self.home.mkdir()
        self.home_patch = mock.patch.object(export_ai_audit.Path, "home", return_value=self.home)
        self.home_patch.start()
        self.config = export_ai_audit.Config(
            log_dir=self.base / "audit",
            author="test.author",
            extra_sources=(),
        )

    def tearDown(self) -> None:
        self.home_patch.stop()
        self.temp.cleanup()

    def write_record(self, path: Path, **fields: object) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(fields) + "\n", encoding="utf-8")
        return path

    def find_paths(self) -> set[Path]:
        return {
            path
            for source, path in export_ai_audit.find_records(self.root, self.config)
            if source.tool == "Copilot CLI"
        }

    def test_nested_events_are_filtered_by_repository_path_or_name(self) -> None:
        copilot = self.home / ".copilot"
        included_by_path = self.write_record(
            copilot / "session-state" / "path-session" / "events.jsonl",
            data={"repositoryPath": str(self.root)},
        )
        excluded = self.write_record(
            copilot / "session-state" / "other-session" / "events.jsonl",
            data={"repositoryPath": str(self.base / "OtherProject")},
        )
        included_by_name = self.write_record(
            copilot / "session-state" / "name-session" / "events.jsonl",
            data={
                "repositoryPath": str(self.base / "different-checkout"),
                "repositoryName": self.root.name,
            },
        )

        paths = self.find_paths()

        self.assertIn(included_by_path, paths)
        self.assertIn(included_by_name, paths)
        self.assertNotIn(excluded, paths)

    def test_nested_event_session_id_comes_from_parent_directory(self) -> None:
        copilot = self.home / ".copilot" / "session-state"
        paths = [
            self.write_record(
                copilot / session_id / "events.jsonl",
                data={"repositoryPath": str(self.root)},
            )
            for session_id in ("session-one", "session-two")
        ]
        facts = [
            export_ai_audit.collect_facts(source, path)
            for source, path in export_ai_audit.find_records(self.root, self.config)
            if path in paths
        ]

        self.assertEqual({fact.session_id for fact in facts}, {"session-one", "session-two"})

    def test_existing_claude_code_source_remains_discoverable(self) -> None:
        project_dir = export_ai_audit.claude_project_dir(self.root)
        transcript = project_dir / "session.jsonl"
        transcript.parent.mkdir(parents=True, exist_ok=True)
        transcript.write_text("{}\n", encoding="utf-8")

        records = export_ai_audit.find_records(self.root, self.config)

        self.assertIn(
            ("Claude Code", transcript),
            {(source.tool, path) for source, path in records},
        )

    def test_existing_historical_copilot_patterns_remain_discoverable(self) -> None:
        copilot = self.home / ".copilot"
        paths = {
            self.write_record(
                copilot / "history-session-state" / "history.json",
                repositoryPath=str(self.root),
            ),
            self.write_record(
                copilot / "session-state" / "legacy.json",
                repositoryPath=str(self.root),
            ),
            self.write_record(
                copilot / "sessions" / "nested" / "session.json",
                repositoryPath=str(self.root),
            ),
            self.write_record(
                copilot / "history" / "nested" / "session.json",
                repositoryPath=str(self.root),
            ),
        }
        log = copilot / "logs" / "nested" / "session.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(str(self.root), encoding="utf-8")
        paths.add(log)

        self.assertEqual(self.find_paths(), paths)


if __name__ == "__main__":
    unittest.main()
