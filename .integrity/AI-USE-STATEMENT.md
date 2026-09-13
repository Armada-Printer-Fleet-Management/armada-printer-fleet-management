# The AI Use Statement

One format, used everywhere agent assistance needs declaring. This file is the source; the
policy and `/commit-message` point here rather than restating the fields.

## Fields

| Field | What it records |
|---|---|
| **Tool** | The product and model. `Claude Code (Opus 5)`, `Copilot CLI (Sonnet 5)`. |
| **Mode** | Where it ran: `Web`, `Desktop`, or `Local`. |
| **Output** | What the agent actually produced. Concrete, past tense, a line or two. |
| **Data** | What was exposed. Sponsor and personal data is never pasted, so this normally reads `none`. Name any anonymisation you did. |
| **Verified** | How *you* checked the output. **Only the developer writes this.** |

Keep it to five lines. This is a declaration, not a report.

## Verified is the field that matters

The other four describe a tool. This one is the claim that a human stands behind the work,
and it is the reason the statement exists at all.

**No agent may write, infer, suggest, or default this field.** An agent that fills it in has
produced a false statement, which is a worse outcome than no statement. If you are an agent
composing one of these: ask, wait, and if the developer has not verified the work, say the
statement is not ready.

Answer it with what you actually did — ran the tests, compared against the vendor's
documentation, traced the logic by hand, tried it against a real printer. "Reviewed the code"
is only true if you read it.

## Data exposure is about the public repository

We use consumer tooling, not an enterprise tenancy with a no-training agreement. Prompts leave
the building. So the answer to **Data** should be `none` because nothing sensitive was pasted,
never because it was pasted and assumed safe.

Separately: a commit statement is published. Generalise it. "a partner's identity provider",
not the vendor's name; "the sponsor's parts database", not the organisation's. The audit log in
OneDrive holds the unabridged record; the commit message does not need to.

---

## In a commit

After the body bullets, before the ticket trailer. Indented fields, no separator line.

```
feat(printer): add Moonraker status polling

- Poll printer state every 5 seconds
- Surface offline printers in the job list

AI Use Statement
  Tool:     Claude Code (Opus 5)
  Mode:     Local
  Output:   polling loop, offline detection, and their unit tests
  Data:     none
  Verified: ran against a local mock printer and compared the
            responses to the vendor's HTTP API documentation

ABC-42 Add printer status polling
```

Omit the whole block when no agent was involved. Disclosure is opt-in and nothing enforces
it — a commit you wrote yourself should carry no statement, and adding one would be its own
kind of false declaration.

## In the README

A short section near the end, covering the project rather than a single change. Update it when
the answer materially changes, not on every commit.

## In a design document

Any document that carries a substantial decision — an architecture decision record, a design
proposal, a milestone report — ends with a statement covering how it was produced.

```
AI Use Statement
  Tool:     Claude Code (Opus 5)
  Mode:     Local
  Output:   drafted the options and trade-offs from a discussion of the constraints
  Data:     none
  Verified: checked each claim about the libraries against their own documentation,
            and rejected two of the options it proposed
```

A document generated without the developer understanding it fails the course's learning
outcomes regardless of what the statement says. See `POLICY.md`.

---

## Reference

This statement format restates the course's requirements. Where the two differ, the course
governs.

> *Policy on the Use of Generative AI.* ENEL 500 — Computer, Electrical, and Software
> Engineering Team Design, Fall 2026. Department of Software and Electrical Engineering,
> University of Calgary. Hamidreza Zareipour. Accessed via D2L.
