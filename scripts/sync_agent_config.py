"""Generate the agent configuration that has no cross-tool standard.

`AGENTS.md` is the canonical instruction file. Copilot, Cursor, Codex, Gemini CLI and
others read it directly. Claude Code does not, so a `CLAUDE.md` beside it imports it
with `@AGENTS.md`. Neither file is generated.

What is generated is the configuration those formats do not cover:

    .claude/skills/<n>/SKILL.md  -> .github/prompts/<n>.prompt.md
    .claude/skills/<n>/SKILL.md  -> .github/skills/<n>/SKILL.md
    <dir>/AGENTS.md              -> <dir>/CLAUDE.md   (a one-line import stub)

Run with --check to report drift without writing.

Standard library only, by design: this runs before dependencies are installed.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

BANNER = "GENERATED FILE - DO NOT EDIT"

SKILLS_DIR = Path(".claude/skills")
PROMPTS_DIR = Path(".github/prompts")
COPILOT_SKILLS_DIR = Path(".github/skills")
ROOT_AGENTS_MD = Path("AGENTS.md")

# Tooling directories, where an AGENTS.md would not be path-scoped project guidance.
EXCLUDED_DIRS = {".git", ".claude", ".github", "node_modules", ".venv", "docs"}


@dataclass(frozen=True)
class Skill:
    """A Claude Code skill, parsed from its SKILL.md."""

    name: str
    description: str
    body: str


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Split YAML-ish frontmatter from a markdown body.

    Handles the flat `key: value` frontmatter that skills use. Returns an empty
    mapping when the document has no frontmatter.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text

    fields: dict[str, str] = {}
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return fields, "\n".join(lines[index + 1 :]).lstrip("\n")
        key, separator, value = line.partition(":")
        if separator:
            parsed_value = value.strip()
            if (
                len(parsed_value) >= 2
                and parsed_value[0] == parsed_value[-1]
                and parsed_value[0] in {"'", '"'}
            ):
                parsed_value = parsed_value[1:-1]
            fields[key.strip()] = parsed_value

    # Unterminated frontmatter: treat the whole document as body.
    return {}, text


def discover_skills(root: Path) -> list[Skill]:
    """Load every skill under .claude/skills/, sorted by name."""
    skills: list[Skill] = []
    skills_root = root / SKILLS_DIR
    if not skills_root.is_dir():
        return skills

    for skill_file in sorted(skills_root.glob("*/SKILL.md")):
        fields, body = parse_frontmatter(skill_file.read_text(encoding="utf-8"))
        skills.append(
            Skill(
                name=fields.get("name") or skill_file.parent.name,
                description=fields.get("description", ""),
                body=body.strip(),
            )
        )
    return skills


def discover_nested_agents(root: Path) -> list[Path]:
    """Find AGENTS.md files below the root, which need a CLAUDE.md import stub."""
    found: list[Path] = []
    for path in sorted(root.rglob("AGENTS.md")):
        relative = path.relative_to(root)
        if relative == ROOT_AGENTS_MD:
            continue
        if any(part in EXCLUDED_DIRS for part in relative.parts):
            continue
        found.append(relative)
    return found


def render_prompt(skill: Skill) -> str:
    """A Copilot prompt file, invoked as /<name> exactly like the Claude skill."""
    source = (SKILLS_DIR / skill.name / "SKILL.md").as_posix()
    return (
        f"---\ndescription: {json.dumps(skill.description)}\n---\n"
        f"<!-- {BANNER}\n"
        f"     Source:    {source}\n"
        f"     Generator: scripts/sync_agent_config.py -->\n"
        f"\n{skill.body}\n"
    )


def render_copilot_skill(skill: Skill) -> str:
    """A Copilot project skill mirrored from the canonical Claude skill."""
    source = (SKILLS_DIR / skill.name / "SKILL.md").as_posix()
    return (
        "---\n"
        f"name: {skill.name}\n"
        f"description: {json.dumps(skill.description)}\n"
        "---\n"
        f"<!-- {BANNER}\n"
        f"     Source:    {source}\n"
        f"     Generator: scripts/sync_agent_config.py -->\n"
        f"\n{skill.body}\n"
    )


def render_claude_stub() -> str:
    """A CLAUDE.md that points Claude Code at the AGENTS.md beside it."""
    return (
        "@AGENTS.md\n"
        "\n"
        f"<!-- {BANNER}\n"
        "     Claude Code does not read AGENTS.md, so this file imports the one\n"
        "     beside it. Put instructions in that AGENTS.md, not here.\n"
        "     Generator: scripts/sync_agent_config.py -->\n"
    )


def build_plan(root: Path) -> dict[Path, str]:
    """Compute every generated file and its expected content."""
    plan: dict[Path, str] = {}

    for skill in discover_skills(root):
        plan[PROMPTS_DIR / f"{skill.name}.prompt.md"] = render_prompt(skill)
        plan[COPILOT_SKILLS_DIR / skill.name / "SKILL.md"] = render_copilot_skill(skill)

    for relative in discover_nested_agents(root):
        plan[relative.parent / "CLAUDE.md"] = render_claude_stub()

    return plan


def orphaned_generated_files(root: Path, planned: set[Path]) -> list[Path]:
    """Generated prompt or Copilot skill files whose source no longer exists."""
    orphaned: list[Path] = []

    prompts_root = root / PROMPTS_DIR
    if prompts_root.is_dir():
        orphaned.extend(
            path.relative_to(root)
            for path in sorted(prompts_root.glob("*.prompt.md"))
            if path.relative_to(root) not in planned
        )

    skills_root = root / COPILOT_SKILLS_DIR
    if skills_root.is_dir():
        orphaned.extend(
            path.relative_to(root)
            for path in sorted(skills_root.glob("*/SKILL.md"))
            if path.relative_to(root) not in planned
        )

    return orphaned


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if generated files differ from their sources. Writes nothing.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Repository root (defaults to the parent of scripts/).",
    )
    args = parser.parse_args()
    root: Path = args.root

    plan = build_plan(root)
    orphaned = orphaned_generated_files(root, set(plan))

    drifted: list[Path] = []
    for relative, expected in sorted(plan.items()):
        target = root / relative
        if target.is_file() and target.read_text(encoding="utf-8") == expected:
            continue
        drifted.append(relative)
        if not args.check:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("w", encoding="utf-8", newline="\n") as handle:
                _ = handle.write(expected)

    if args.check:
        if drifted or orphaned:
            for relative in drifted:
                print(f"out of date: {relative.as_posix()}")
            for relative in orphaned:
                print(f"orphaned:    {relative.as_posix()}")
            print("\nRun: python scripts/sync_agent_config.py")
            return 1
        print(f"up to date ({len(plan)} generated files)")
        return 0

    for relative in orphaned:
        (root / relative).unlink()
        print(f"removed  {relative.as_posix()}")
    for relative in drifted:
        print(f"wrote    {relative.as_posix()}")
    if not drifted and not orphaned:
        print(f"up to date ({len(plan)} generated files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
