# AI use policy

**Required reading before your first commit.** This applies to every developer and every agent
working in this repository.

Agent assistance is permitted and normal here. What is not permitted is using it invisibly,
using it without checking the result, or using it in a way that means nobody on the team can
explain their own code. This document states those limits as rules an agent can act on.

The statement format every rule below refers to is in [`AI-USE-STATEMENT.md`](AI-USE-STATEMENT.md).

---

## 1. Valid use, and what follows from it

Agents may draft code, tests, documentation and review comments; explain unfamiliar code;
propose designs; and carry out mechanical refactors.

Every one of those creates the same obligation on the developer who accepts the output:

- **You are the author.** You committed it, you defend it, and you can be asked to explain any
  line of it. "The agent wrote it" is not an answer to a question about your own code.
- **Understand it before you commit it.** If you cannot explain what a generated function does
  and why it is shaped that way, it is not ready, no matter that the tests pass.
- **Verify it.** See rule 2.
- **Declare it.** See rule 3.

## 2. Fact-check generated content and its sources

Agents state wrong things fluently. Treat output as a draft from someone confident and
unreliable.

- **Verify claims about libraries, APIs and tools against their own documentation.** Not
  against the agent's summary of that documentation.
- **Check that cited sources exist and say what they were claimed to say.** Fabricated
  references and invented version numbers are common failure modes.
- **Run the code.** A test that was generated alongside the code it tests proves less than you
  would like — it can encode the same misunderstanding twice.
- **A dependency needs its repository, its maintenance signals and its licence checked by a
  human** before it enters the project. This is already required by `AGENTS.md`; agent
  suggestion does not shortcut it.

## 3. Nothing undisclosed

**AI-assisted work is never submitted without an AI Use Statement.** Three places require one:

| Where | When |
|---|---|
| Commit message | Any commit whose content an agent helped produce |
| `README.md` | The project's overall statement, kept current |
| Design and decision documents | Any document carrying a substantial decision or milestone — architecture decision records, design proposals, reports |

Disclosure is **opt-in and unenforced**. No hook and no CI job checks for a statement, because
a commit you wrote unaided should not carry one. That makes this an honesty requirement rather
than a mechanical one, which is the only form it can take.

**The `Verified:` field is written by the developer, never by an agent.** An agent that fills
it in has fabricated a human's assurance. If you are an agent and the developer has not
answered it, the correct output is "this is not ready", not a plausible sentence.

## 4. Understand what you are building

**This rule does not limit what an agent may do.** Use the full capability of the tool. Let it
write the whole module, generate the tests, do the refactor, draft the document. Nothing here
asks an agent to hold back, work slower, or produce less than it can.

**The developer must own the design and engineering decisions.** The agent proposes, informs,
and builds; the choice of what to build and how it is shaped belongs to the person accountable
for it. That ownership is what the rest of this rule protects.

What it requires is that **the developer ends up understanding the result and knowing what the
alternatives were.** The failure this prevents is not "too much AI" — it is a developer who
cannot say what their code does, or why it is built this way rather than another way. Volume of
generated code is not the problem; unexamined generated code is.

So, alongside the output:

- **Explain the non-obvious parts.** If generated logic is not self-evident, the agent walks
  the developer through it. That conversation is as much the deliverable as the code.
- **Name the alternatives.** A developer should be able to say what else was considered and why
  this won. An agent that produces one design and no context has left the developer unable to
  defend it, however good the design is.
- **Flag what the developer should look at.** Say where the risk is, what is untested, what was
  assumed. Confident silence is the real hazard.

### Larger design decisions go through plan mode

Anything that shapes the system rather than implementing it — architecture, a new dependency,
a data model, a public interface, a cross-cutting refactor — is decided **in plan mode, with a
questionnaire survey of the options** before any code is written.

That means: enumerate the realistic options, give the trade-offs of each, ask the developer to
choose through an explicit question rather than inferring their preference, and only then
build. The developer picks; the agent informs the pick.

**A fresh session whose scope or design is significant starts in plan mode.** If the developer
has not enabled it, the agent enables it rather than beginning to implement. Small, well-scoped
changes do not need this — a typo fix is not an architecture decision.

Decisions reached this way are recorded in the ticket the work is committed under, which is what
makes them reviewable later by someone who was not in the conversation.

## 5. Confidential material

- **Never paste sponsor or personal data into a prompt.** Describe the shape of data, not its
  contents. "A parts table keyed by an eight-character identifier" is enough; a real extract is
  not permitted.
- **Third-party library source lives outside this repository.** Forks, open source and closed
  alike, belong in sibling directories, never inside this tree. Some are confidential. An agent
  must confirm with the developer before reading any of it, and must never copy it in.
- **Deployment-specific values are configuration**, under `config/`, ignored by default.
- **A commit message is published.** Generalise sponsor, vendor, and personal names in the AI
  Use Statement and everywhere else. The audit log holds the full record; the public repository
  does not need it.

We do not use enterprise AI tooling with a no-training agreement. Assume anything in a prompt
has left the building permanently.

## 6. The audit trail

Session transcripts are exported to the team's shared log by
[`scripts/export_ai_audit.py`](../scripts/export_ai_audit.py), automatically when a Claude Code
session ends and on demand via `/export-ai-integrity`.

- Configure it during `/onboarding`. An unconfigured machine produces no evidence, so the
  script fails loudly rather than skipping.
- **Claude Code and Copilot CLI records are both exported.** Claude Code transcripts are parsed
  for their facts; Copilot's are copied verbatim and filtered to this repository, since its
  format is not one we have pinned down. Other tools can be added through
  `AI_AUDIT_EXTRA_SOURCES`.
- The export is **not redacted**. It is confidential to the team, and a partial redactor would
  only create false confidence.
- Transcripts plus commit statements are the coverage. Neither alone is enough: the log shows
  what was asked, the statements show what was accepted and checked.

Only Claude Code can trigger the export automatically on session end. **After a Copilot
session, run `/export-ai-integrity` yourself** — nothing will do it for you.

---

## What is mechanical, and what is not

Honest accounting, because a policy that oversells its enforcement invites people to rely on
it:

| Control | Mechanical? |
|---|---|
| `config/` ignored by default | **Yes** — `.gitignore` |
| Secret scanning on staged changes | **Yes** — `gitleaks` in `.githooks/pre-commit` |
| Commit format and no agent attribution | **Yes** — `.githooks/commit-msg` |
| Transcript export on session end | **Yes**, for Claude Code. Copilot must be exported by hand. |
| Presence of an AI Use Statement | **No** — deliberately, since it is opt-in |
| Truth of a `Verified:` answer | **No** — it is a personal assurance |
| Starting in plan mode for design work | **No** — instruction to the agent |
| Everything in rules 1, 2, 4 and 5 | **No** — instruction only |

Copilot honours no permission mechanism, and a shell command can reach past an agent's file
tools. The rules above are the control; the hooks catch a narrow set of accidents.

---

## Reference

This document restates the course's requirements for this repository. Where the two differ,
the course governs.

> *Policy on the Use of Generative AI.* ENEL 500 — Computer, Electrical, and Software
> Engineering Team Design, Fall 2026. Department of Software and Electrical Engineering,
> University of Calgary. Hamidreza Zareipour. Accessed via D2L.
