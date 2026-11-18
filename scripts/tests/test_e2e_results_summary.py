"""Tests for scripts/e2e_results_summary.py: what the e2e results summary says for pytest's
JUnit XML. The XML below is the shape pytest writes for each outcome.

Standard library only, like the script:

    python -m unittest discover -s scripts/tests
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import e2e_results_summary

PASS = '<testcase classname="e2e.test_a" name="test_pass"/>'
FAIL = '<testcase classname="e2e.test_a" name="test_fail"><failure message="assert False"/></testcase>'
ERROR = (
    '<testcase classname="e2e.test_b" name="test_error">'
    '<error message="failed on setup"/></testcase>'
)
XFAIL = (
    '<testcase classname="e2e.test_b" name="test_xfail">'
    '<skipped type="pytest.xfail" message="needs a finished flow"/></testcase>'
)
XFAIL_NO_REASON = (
    '<testcase classname="e2e.test_b" name="test_xfail_no_reason">'
    '<skipped type="pytest.xfail" message=""/></testcase>'
)
XPASS_STRICT = (
    '<testcase classname="e2e.test_c" name="test_xpass">'
    '<failure message="[XPASS(strict)] x">[XPASS(strict)] x</failure></testcase>'
)
SKIP = (
    '<testcase classname="e2e.test_c" name="test_skip">'
    '<skipped type="pytest.skip" message="s"/></testcase>'
)


class SummaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.results = Path(self.temp.name) / "e2e-results.xml"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def summarise(self, *cases: str) -> str:
        self.results.write_text(
            '<testsuites><testsuite name="pytest">' + "".join(cases) + "</testsuite></testsuites>",
            encoding="utf-8",
        )
        return e2e_results_summary.summary(self.results)

    def test_counts_each_outcome(self) -> None:
        text = self.summarise(PASS, PASS, FAIL, ERROR, XFAIL, SKIP)

        self.assertIn("| Passed | 2 |", text)
        self.assertIn("| Failed | 2 |", text)
        self.assertIn("| Expected to fail | 1 |", text)
        self.assertIn("| Skipped | 1 |", text)

    def test_lists_failures_and_errors_by_name(self) -> None:
        text = self.summarise(PASS, FAIL, ERROR)

        self.assertIn("Failing:", text)
        self.assertIn("- `e2e.test_a::test_fail`", text)
        self.assertIn("- `e2e.test_b::test_error`", text)
        self.assertNotIn("test_pass`", text)

    def test_no_failing_section_when_every_test_passes(self) -> None:
        text = self.summarise(PASS, XFAIL)

        self.assertNotIn("Failing:", text)

    def test_a_strict_xpass_counts_as_a_failure(self) -> None:
        text = self.summarise(XPASS_STRICT)

        self.assertIn("| Failed | 1 |", text)
        self.assertIn("| Expected to fail | 0 |", text)
        self.assertIn("- `e2e.test_c::test_xpass`", text)

    def test_lists_expected_failures_with_their_reason(self) -> None:
        text = self.summarise(PASS, XFAIL)

        self.assertIn("Expected to fail:", text)
        self.assertIn("- `e2e.test_b::test_xfail`: needs a finished flow", text)

    def test_an_expected_failure_without_a_reason_is_listed_by_name_alone(self) -> None:
        text = self.summarise(XFAIL_NO_REASON)

        self.assertIn("- `e2e.test_b::test_xfail_no_reason`\n", text)
        self.assertNotIn("test_xfail_no_reason`:", text)

    def test_no_expected_to_fail_section_without_expected_failures(self) -> None:
        text = self.summarise(PASS, FAIL)

        self.assertNotIn("Expected to fail:", text)

    def test_a_strict_xpass_is_listed_as_failing_only(self) -> None:
        text = self.summarise(XPASS_STRICT)

        self.assertIn("Failing:", text)
        self.assertNotIn("Expected to fail:", text)

    def test_a_missing_results_file_says_the_suite_did_not_run(self) -> None:
        text = e2e_results_summary.summary(self.results)

        self.assertTrue(text.startswith(e2e_results_summary.MARKER + "\n"))
        self.assertIn("The suite did not run", text)
        self.assertNotIn("| Result |", text)


if __name__ == "__main__":
    unittest.main()
