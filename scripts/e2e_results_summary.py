#!/usr/bin/env python3
"""Writes the e2e smoke tests' results as Markdown, from pytest's JUnit XML, for e2e.ci.yml to
put on the run's summary page and in its pull request comment. Standard library only.

Usage:
    python scripts/e2e_results_summary.py <junit xml> <markdown out>
"""

from __future__ import annotations

import pathlib
import sys
import xml.etree.ElementTree as ET

# The comment step finds its earlier comment by this first line.
MARKER = "<!-- server-e2e -->"
OUTCOMES = ("Passed", "Failed", "Expected to fail", "Skipped")


def summary(results: pathlib.Path) -> str:
    lines = [MARKER, "### Server e2e smoke tests", ""]
    if not results.is_file():
        lines.append("_The suite did not run. See the job's log._")
        return "\n".join(lines) + "\n"

    counts = dict.fromkeys(OUTCOMES, 0)
    failing: list[str] = []
    expected_to_fail: list[str] = []
    for case in ET.parse(results).iter("testcase"):
        name = f"`{case.get('classname')}::{case.get('name')}`"
        skipped = case.find("skipped")
        # pytest writes a strict XPASS as a failure, so it is counted as one here too.
        if case.find("failure") is not None or case.find("error") is not None:
            counts["Failed"] += 1
            failing.append(name)
        elif skipped is not None and skipped.get("type") == "pytest.xfail":
            counts["Expected to fail"] += 1
            # The mark's reason, which names what the flow is waiting on.
            reason = skipped.get("message", "")
            expected_to_fail.append(f"{name}: {reason}" if reason else name)
        elif skipped is not None:
            counts["Skipped"] += 1
        else:
            counts["Passed"] += 1

    lines += ["| Result | Tests |", "| --- | --- |"]
    lines += [f"| {outcome} | {count} |" for outcome, count in counts.items()]
    for heading, tests in (("Failing", failing), ("Expected to fail", expected_to_fail)):
        if tests:
            lines += ["", f"{heading}:", ""] + [f"- {test}" for test in tests]
    return "\n".join(lines) + "\n"


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    pathlib.Path(sys.argv[2]).write_text(summary(pathlib.Path(sys.argv[1])), encoding="utf-8")


if __name__ == "__main__":
    main()
