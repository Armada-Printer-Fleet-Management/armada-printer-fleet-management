"""Export agent session transcripts to the team's AI audit log.

This is a capstone project, and its use of AI assistants has to be evidenced rather
than asserted. This script copies raw session transcripts to a shared location,
alongside a summary of the facts it can establish mechanically.

    <AI_AUDIT_LOG_DIR>/ai-audit-log/<author>/
        INDEX.md
        <date>_<tool>_<session-id>/
            <original record file>
            SESSION.md

Claude Code transcripts are parsed for their facts. Records from other tools are
copied verbatim without a schema being assumed, and filtered to this repository by
whether they mention its path.

The export is keyed by session id and overwrites in place, so running it repeatedly
refreshes one directory per session rather than accumulating copies. A SessionEnd
hook can therefore fire as often as it likes.

Transcripts are copied verbatim. Redaction is deliberately not attempted: an
imperfect redactor would create false confidence in a folder that is confidential
to the team anyway. The place where sensitive detail must be generalised is the
public commit message, which `/commit-message` handles.

SESSION.md never carries a filled-in `Verified:` field. Only the developer can
answer that, and `/export-ai-integrity` exists to ask them.

Standard library only, by design: this runs from a git hook and before dependencies
are installed.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterator, cast

LOG_DIR_VAR = "AI_AUDIT_LOG_DIR"
AUTHOR_VAR = "AI_AUDIT_AUTHOR"
EXTRA_SOURCES_VAR = "AI_AUDIT_EXTRA_SOURCES"

# The only .env keys this script reads. Everything else in that file stays unread.
OWN_SETTINGS = frozenset({LOG_DIR_VAR, AUTHOR_VAR, EXTRA_SOURCES_VAR})

AUDIT_DIR_NAME = "ai-audit-log"

UNFILLED = "<!-- UNFILLED: only the developer may answer this. Run /export-ai-integrity. -->"

# Claude Code names a session's model on each assistant message. Failed turns carry
# this placeholder instead, which says nothing about what was used.
SYNTHETIC_MODEL = "<synthetic>"


# ─── configuration ───────────────────────────────────────────────────────────


def read_env_keys(path: Path, wanted: frozenset[str]) -> dict[str, str]:
    """Read only the named KEY=value pairs from a .env file.

    The file holds unrelated secrets. Reading just the keys this script uses keeps
    the rest out of memory, out of tracebacks, and out of anything it prints.
    """
    values: dict[str, str] = {}
    if not path.is_file():
        return values

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if not separator:
            continue
        name = key.strip()
        if name in wanted:
            values[name] = value.strip().strip("\"'")
    return values


@dataclass(frozen=True)
class Config:
    log_dir: Path
    author: str
    extra_sources: tuple[Path, ...]


class ConfigError(Exception):
    """The audit log is not usable. Always reported; never swallowed."""


def load_config(root: Path) -> Config:
    """Resolve settings from the environment, falling back to the root .env.

    Raises ConfigError with instructions rather than returning a partial config —
    a half-configured audit log silently produces no evidence.
    """
    from_file = read_env_keys(root / ".env", OWN_SETTINGS)

    def setting(name: str) -> str:
        return (os.environ.get(name) or from_file.get(name) or "").strip()

    problems: list[str] = []

    raw_log_dir = setting(LOG_DIR_VAR)
    log_dir = Path(raw_log_dir).expanduser() if raw_log_dir else None
    if log_dir is None:
        problems.append(f"{LOG_DIR_VAR} is not set.")
    elif not log_dir.is_dir():
        problems.append(f"{LOG_DIR_VAR} points at {log_dir}, which does not exist.")

    author = setting(AUTHOR_VAR)
    if not author:
        problems.append(f"{AUTHOR_VAR} is not set.")
    elif "." not in author:
        problems.append(f"{AUTHOR_VAR} is '{author}'; expected firstname.lastname.")

    if problems:
        raise ConfigError("\n".join(problems))

    extra: list[Path] = []
    for entry in setting(EXTRA_SOURCES_VAR).split(os.pathsep):
        candidate = entry.strip()
        if candidate:
            extra.append(Path(candidate).expanduser())

    assert log_dir is not None  # guaranteed by the problems check above
    return Config(log_dir=log_dir, author=author, extra_sources=tuple(extra))


# ─── locating transcripts ────────────────────────────────────────────────────


@dataclass(frozen=True)
class Source:
    """A place one tool keeps its session records.

    `structured` marks the Claude Code transcript format, which this script parses.
    Everything else is copied opaquely: the file is evidence whether or not we can
    read its schema, and guessing at a schema we have not verified would be worse
    than admitting we do not know it.
    """

    tool: str
    directory: Path
    patterns: tuple[str, ...]
    structured: bool
    scoped_by_directory: bool


def claude_project_dir(root: Path) -> Path:
    """Where Claude Code stores this repository's transcripts.

    The directory name is the absolute path with separators and the drive colon
    replaced by hyphens. Derived rather than hardcoded so it holds on any machine.
    """
    slug = str(root.resolve())
    for character in ("\\", "/", ":"):
        slug = slug.replace(character, "-")
    return Path.home() / ".claude" / "projects" / slug


def known_sources(root: Path, config: Config) -> list[Source]:
    """Every place a session record for this repository might live.

    Copilot CLI's layout is not pinned down here. Several plausible locations are
    searched and whichever exists is used, because the alternative is a hardcoded
    path that silently exports nothing the day it changes.
    """
    copilot = Path.home() / ".copilot"
    sources = [
        Source(
            tool="Claude Code",
            directory=claude_project_dir(root),
            patterns=("*.jsonl",),
            structured=True,
            scoped_by_directory=True,
        ),
        Source(
            tool="Copilot CLI",
            directory=copilot,
            patterns=(
                "history-session-state/*.json",
                "session-state/*.json",
                "sessions/**/*.json",
                "history/**/*.json",
                "logs/**/*.log",
            ),
            structured=False,
            scoped_by_directory=False,
        ),
        Source(
            tool="manual",
            directory=root / ".integrity" / "transcripts",
            patterns=("*.jsonl", "*.json", "*.md", "*.txt"),
            structured=False,
            scoped_by_directory=True,
        ),
    ]

    for extra in config.extra_sources:
        sources.append(
            Source(
                tool="other",
                directory=extra,
                patterns=("**/*.jsonl", "**/*.json", "**/*.log", "**/*.md"),
                structured=False,
                scoped_by_directory=True,
            )
        )
    return sources


def mentions_repository(path: Path, root: Path) -> bool:
    """Whether a record refers to this repository.

    Sources that are not namespaced per project hold sessions from every project on
    the machine. Only this repository's belong in its audit log, and the repository
    path is the one marker every tool records.
    """
    needles = {str(root.resolve()), str(root.resolve()).replace("\\", "/"), root.name}
    encoded = {needle.replace("\\", "\\\\") for needle in needles}

    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    return any(needle in text for needle in needles | encoded)


def find_records(root: Path, config: Config) -> list[tuple[Source, Path]]:
    """Every session record belonging to this repository, across all tools."""
    found: list[tuple[Source, Path]] = []
    seen: set[Path] = set()

    for source in known_sources(root, config):
        if not source.directory.is_dir():
            continue
        for pattern in source.patterns:
            for path in sorted(source.directory.glob(pattern)):
                if not path.is_file():
                    continue
                resolved = path.resolve()
                if resolved in seen:
                    continue
                if not source.scoped_by_directory and not mentions_repository(path, root):
                    continue
                seen.add(resolved)
                found.append((source, path))
    return found


# ─── reading a transcript ────────────────────────────────────────────────────


@dataclass
class SessionFacts:
    """What can be established from a record without interpreting it."""

    session_id: str
    source: Path
    tool: str
    parsed: bool = True
    started: str = ""
    ended: str = ""
    models: set[str] = field(default_factory=set[str])
    branches: set[str] = field(default_factory=set[str])
    tool_versions: set[str] = field(default_factory=set[str])
    entrypoints: set[str] = field(default_factory=set[str])
    prompts: int = 0

    @property
    def date(self) -> str:
        return self.started[:10] if self.started else "undated"

    @property
    def directory_name(self) -> str:
        slug = self.tool.lower().replace(" ", "-")
        return f"{self.date}_{slug}_{self.session_id[:8]}"


def as_object(value: object) -> dict[str, object] | None:
    """Narrow a decoded JSON value to an object.

    `json.loads` is untyped, so every field pulled out of a record needs narrowing
    before it can be used under strict type checking.
    """
    if isinstance(value, dict):
        return cast("dict[str, object]", value)
    return None


def as_list(value: object) -> list[object] | None:
    if isinstance(value, list):
        return cast("list[object]", value)
    return None


def text_field(record: dict[str, object], key: str) -> str | None:
    """A non-empty string field, or None if it is absent or another type."""
    value = record.get(key)
    return value if isinstance(value, str) and value else None


def read_records(path: Path) -> Iterator[dict[str, object]]:
    """Stream a transcript, skipping lines that are not readable JSON objects.

    Transcripts are appended live, so the final line may be a partial write.
    """
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                decoded: object = json.loads(line)
            except json.JSONDecodeError:
                continue
            record = as_object(decoded)
            if record is not None:
                yield record


def collect_facts(source: Source, path: Path) -> SessionFacts:
    if not source.structured:
        return opaque_facts(source, path)

    facts = SessionFacts(session_id=path.stem, source=path, tool=source.tool)

    for record in read_records(path):
        session_id = text_field(record, "sessionId")
        if session_id:
            facts.session_id = session_id

        timestamp = text_field(record, "timestamp")
        if timestamp:
            if not facts.started or timestamp < facts.started:
                facts.started = timestamp
            if timestamp > facts.ended:
                facts.ended = timestamp

        for key, target in (
            ("gitBranch", facts.branches),
            ("version", facts.tool_versions),
            ("entrypoint", facts.entrypoints),
        ):
            value = text_field(record, key)
            if value:
                target.add(value)

        message = as_object(record.get("message"))
        if message is None:
            continue

        model = text_field(message, "model")
        if model and model != SYNTHETIC_MODEL:
            facts.models.add(model)

        if record.get("type") == "user" and not record.get("isMeta"):
            if is_human_prompt(message):
                facts.prompts += 1

    return facts


def opaque_facts(source: Source, path: Path) -> SessionFacts:
    """Facts for a record whose format this script does not parse.

    The file's own timestamp dates it and its name identifies it. Nothing else is
    claimed, because nothing else has been established.
    """
    modified = datetime.fromtimestamp(path.stat().st_mtime).astimezone()
    return SessionFacts(
        session_id=path.stem,
        source=path,
        tool=source.tool,
        parsed=False,
        started=modified.strftime("%Y-%m-%dT%H:%M:%S%z"),
        ended=modified.strftime("%Y-%m-%dT%H:%M:%S%z"),
    )


def is_human_prompt(message: dict[str, object]) -> bool:
    """Whether a user record is something a person typed.

    Tool results are also recorded as user messages. Counting them would inflate
    the figure in a document whose only value is being accurate.
    """
    content = message.get("content")
    if isinstance(content, str):
        return bool(content.strip())

    blocks = as_list(content)
    if blocks is None:
        return False
    return any(
        (block := as_object(item)) is not None and block.get("type") == "text"
        for item in blocks
    )


# ─── writing the export ──────────────────────────────────────────────────────


def render_session(facts: SessionFacts, author: str) -> str:
    """The per-session summary. Every field here is machine-derived except Verified."""

    def listed(values: set[str]) -> str:
        return ", ".join(sorted(values)) if values else "unknown"

    entrypoints = listed(facts.entrypoints)
    mode = "Local" if entrypoints == "cli" else entrypoints

    if facts.parsed:
        version = listed(facts.tool_versions)
        detail = [
            f"| Git branch | {listed(facts.branches)} |",
            f"| Human prompts | {facts.prompts} |",
        ]
        tool = f"{facts.tool} (version {version})"
        model = listed(facts.models)
        note = (
            "Everything above the verification field was derived from the transcript by\n"
            "`scripts/export_ai_audit.py`."
        )
    else:
        detail = []
        tool = facts.tool
        mode = "unknown"
        model = "unknown"
        note = (
            f"This record was copied verbatim. `{facts.source.name}` is in a format this script\n"
            "does not parse, so its date comes from the file's own timestamp and no further\n"
            "claim is made about it. The file itself is the evidence."
        )

    rows = "\n".join(
        [
            f"| Developer | {author} |",
            f"| Tool | {facts.tool} |",
            f"| Started | {facts.started or 'unknown'} |",
            f"| Ended | {facts.ended or 'unknown'} |",
            *detail,
            f"| Source file | `{facts.source.name}` |",
        ]
    )

    return f"""# Session {facts.session_id}

| | |
|---|---|
{rows}

## AI Use Statement

- **Tool:** {tool}
- **Mode:** {mode}
- **Model:** {model}
- **Output:** see the copied record for what was asked and produced.
- **Data exposure:** no sponsor or personal data is permitted in prompts under
  `.integrity/POLICY.md`. This field records adherence, not a scan.
- **Human verification:**

{UNFILLED}

## About this file

{note} The verification field is the developer's own account of how they checked the work,
and no agent may write it.
"""


def render_index(author: str, sessions: list[SessionFacts]) -> str:
    generated = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
    lines = [
        f"# AI audit log — {author}",
        "",
        "Agent session transcripts for the capstone project, exported by",
        "`scripts/export_ai_audit.py`. Confidential to the team.",
        "",
        f"Rebuilt {generated}. {len(sessions)} session(s).",
        "",
        "| Session | Date | Tool | Branch | Human prompts | Models |",
        "|---|---|---|---|---|---|",
    ]

    for facts in sorted(sessions, key=lambda item: item.directory_name, reverse=True):
        branches = ", ".join(sorted(facts.branches)) or "—"
        models = ", ".join(sorted(facts.models)) or "—"
        prompts = str(facts.prompts) if facts.parsed else "—"
        lines.append(
            f"| [`{facts.session_id[:8]}`]({facts.directory_name}/SESSION.md) "
            f"| {facts.date} | {facts.tool} | {branches} | {prompts} | {models} |"
        )

    lines.append("")
    return "\n".join(lines)


def is_unchanged(source: Path, target: Path) -> bool:
    """Whether a copy can be skipped. Size and mtime are enough for append-only logs."""
    if not target.is_file():
        return False
    source_stat = source.stat()
    target_stat = target.stat()
    return (
        source_stat.st_size == target_stat.st_size
        and int(source_stat.st_mtime) == int(target_stat.st_mtime)
    )


def preserve_verification(existing: Path, rendered: str) -> str:
    """Carry a developer's verification answer across re-exports.

    Without this, every SessionEnd would erase the one field the developer had to
    supply by hand.
    """
    if not existing.is_file():
        return rendered

    previous = existing.read_text(encoding="utf-8")
    marker = "- **Human verification:**"
    _, separator, answer = previous.partition(marker)
    if not separator or UNFILLED in answer:
        return rendered

    head, marker_found, _ = rendered.partition(marker)
    if not marker_found:
        return rendered
    return head + marker + answer


# ─── main ────────────────────────────────────────────────────────────────────


def apply_verification(destination: Path, exported: list[SessionFacts], answer: str) -> tuple[int, int]:
    """Write the developer's verification answer into sessions still missing one.

    It arrives as a command-line argument so that the words originate with the developer.
    Sessions already carrying an answer are left alone, so re-running cannot overwrite one.
    """
    body = "\n".join(f"  {line}".rstrip() for line in answer.strip().splitlines())
    filled = 0
    already = 0
    for facts in exported:
        session_file = destination / facts.directory_name / "SESSION.md"
        if not session_file.is_file():
            continue
        text = session_file.read_text(encoding="utf-8")
        if UNFILLED not in text:
            already += 1
            continue
        _ = session_file.write_text(text.replace(UNFILLED, body), encoding="utf-8", newline="\n")
        filled += 1
    return filled, already


def export(
    root: Path,
    config: Config,
    *,
    dry_run: bool,
    quiet: bool,
    only: str | None,
    verified: str | None,
) -> int:
    destination = config.log_dir / AUDIT_DIR_NAME / config.author
    records = find_records(root, config)

    if not records:
        print("No session records found for this repository. Nothing to export.")
        return 0

    exported: list[SessionFacts] = []
    copied = 0
    skipped = 0

    for source, path in records:
        facts = collect_facts(source, path)
        if only and not facts.session_id.startswith(only):
            continue
        exported.append(facts)

        session_dir = destination / facts.directory_name
        transcript_target = session_dir / path.name
        session_target = session_dir / "SESSION.md"

        if is_unchanged(path, transcript_target):
            skipped += 1
            if not quiet:
                print(f"unchanged  {facts.directory_name}")
            continue

        copied += 1
        if not quiet:
            print(f"exporting  {facts.directory_name}")
        if dry_run:
            continue

        session_dir.mkdir(parents=True, exist_ok=True)
        _ = shutil.copy2(path, transcript_target)
        content = preserve_verification(session_target, render_session(facts, config.author))
        _ = session_target.write_text(content, encoding="utf-8", newline="\n")

    if only and not exported:
        print(f"No session matching '{only}'.", file=sys.stderr)
        return 1

    if not dry_run:
        destination.mkdir(parents=True, exist_ok=True)
        index = destination / "INDEX.md"
        _ = index.write_text(render_index(config.author, exported), encoding="utf-8", newline="\n")

    prefix = "would export" if dry_run else "exported"
    print(f"{prefix} {copied}, unchanged {skipped}  ->  {destination}")

    if verified and dry_run:
        print("verification not written: --dry-run")
    elif verified:
        filled, already = apply_verification(destination, exported, verified)
        summary = f"verification written to {filled} session(s)"
        if already:
            summary += f", {already} already answered and left unchanged"
        print(summary)

    if not dry_run:
        unfilled = [facts for facts in exported if needs_verification(destination, facts)]
        if unfilled:
            print(f"\n{len(unfilled)} session(s) still need a human verification answer:")
            for facts in unfilled:
                print(f"  {facts.directory_name}")
            print("Run /export-ai-integrity to supply it.")

    return 0


def needs_verification(destination: Path, facts: SessionFacts) -> bool:
    """Whether a session's SESSION.md still holds the unfilled marker."""
    session_file = destination / facts.directory_name / "SESSION.md"
    if not session_file.is_file():
        return False
    return UNFILLED in session_file.read_text(encoding="utf-8")


def report_config_error(error: ConfigError) -> None:
    """Always loud. An unconfigured audit log is the failure this script prevents."""
    print("", file=sys.stderr)
    print("!" * 74, file=sys.stderr)
    # ASCII only: this must stay readable on a Windows console using a legacy codepage.
    print("AI AUDIT LOG IS NOT CONFIGURED - nothing was exported.", file=sys.stderr)
    print("", file=sys.stderr)
    for line in str(error).splitlines():
        print(f"  {line}", file=sys.stderr)
    print("", file=sys.stderr)
    print("  This project requires an audit trail of agent sessions. Run /onboarding", file=sys.stderr)
    print(f"  to set {LOG_DIR_VAR} and {AUTHOR_VAR} in your .env file.", file=sys.stderr)
    print("", file=sys.stderr)
    print(f"  {LOG_DIR_VAR} is the OneDrive shortcut to the shared {AUDIT_DIR_NAME} folder.", file=sys.stderr)
    print("!" * 74, file=sys.stderr)
    print("", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-session output on success. Configuration problems are still reported.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be exported without writing anything.",
    )
    parser.add_argument(
        "--session",
        metavar="ID",
        help="Export only the session whose id starts with ID.",
    )
    parser.add_argument(
        "--verified",
        metavar="TEXT",
        help=(
            "How you checked this session's output. Written into every exported session "
            "that still needs an answer; sessions already answered are left alone. "
            "Supply this yourself - an agent must never write it on your behalf."
        ),
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Repository root (defaults to the parent of scripts/).",
    )
    args = parser.parse_args()

    try:
        config = load_config(args.root)
    except ConfigError as error:
        report_config_error(error)
        return 1

    return export(
        args.root,
        config,
        dry_run=bool(args.dry_run),
        quiet=bool(args.quiet),
        only=args.session,
        verified=args.verified,
    )


if __name__ == "__main__":
    sys.exit(main())
