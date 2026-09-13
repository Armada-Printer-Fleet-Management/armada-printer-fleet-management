# Academic integrity

This project is coursework, and its use of AI coding assistants is subject to the course's
academic integrity rules. This directory holds the policy and the artefacts that demonstrate
compliance with it.

## Contents

| Path | What it is |
|---|---|
| [`POLICY.md`](POLICY.md) | **Required reading.** The course's AI-use rules, written as instructions an agent can act on. |
| [`AI-USE-STATEMENT.md`](AI-USE-STATEMENT.md) | The declaration format used in commits, the README, and design documents. |
| `transcripts/` | Gitignored. Drop a session record here and the exporter will pick it up. |

## How the pieces fit

Disclosure and evidence are separate mechanisms, and neither alone would be enough:

- **AI Use Statements** say what was accepted and how a human checked it. They live in commit
  messages, `README.md`, and design documents. They are short, public, and opt-in.
- **The audit log** says what was actually asked and produced. Session transcripts are exported
  to the team's shared OneDrive by `../scripts/export_ai_audit.py`, automatically when a Claude
  Code session ends and on demand via `/export-ai-integrity`. It is complete, unredacted, and
  confidential to the team.

A statement without the log is an unverifiable claim. The log without statements is a pile of
JSON nobody has vouched for.

## The `Verified:` field

Every statement ends with the developer's own account of how they checked the output. **No
agent may write it** — an agent that fills it in has fabricated a human's assurance, which is
worse than leaving it blank. Both `/commit-message` and `/export-ai-integrity` are written to
ask and wait.

## What is enforced mechanically

Little of this, deliberately. `POLICY.md` closes with an honest table of which controls are
mechanical and which are instruction. In short:

- `.githooks/commit-msg` enforces the commit format and rejects `Co-Authored-By` trailers.
- `.githooks/pre-commit` runs `gitleaks` over staged changes.
- `.gitignore` ignores `config/` by default, so deployment-specific values cannot be committed
  by accident.
- The presence and truth of an AI Use Statement are **not** enforced. Disclosure is opt-in
  because a commit written unaided should not carry one.

## Reference

> *Policy on the Use of Generative AI.* ENEL 500 — Computer, Electrical, and Software
> Engineering Team Design, Fall 2026. Department of Software and Electrical Engineering,
> University of Calgary. Hamidreza Zareipour. Accessed via D2L.
