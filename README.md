# Capstone

Fleet management software for 3D printers, built as a university capstone project.

A monorepo delivering three applications — a server, a web app, and a desktop app.

| Application | Path            | Stack                                          |
| ----------- | --------------- | ---------------------------------------------- |
| Server      | `apps/server/`  | Python, ASGI, ConnectRPC                       |
| Web app     | `apps/web/`     | React, TypeScript, Vite                        |
| Desktop app | `apps/desktop/` | Python backend (pywebview) with a React frontend |

The web and desktop apps are separate applications. They communicate only through the server,
and share code through `packages/ui-kit` and `packages/api-client` rather than by importing one
another.

## Status

Early. The repository currently holds governance, tooling and documented decisions; application
code is the next phase.

## Getting started

Run **`/onboarding`** in Claude Code or Copilot. It installs the toolchain, wires the git
hooks, prepares configuration, and opens the documentation.

Everything it does is also written out in `.claude/skills/onboarding/SKILL.md` if you would
rather follow it by hand.

JavaScript dependencies are installed once from the repository root with `pnpm install`; the
root workspace links `apps/web`, `apps/desktop/frontend`, and shared packages such as
`packages/ui-kit`.

## Documentation

| Where                  | What                                                                  |
| ---------------------- | --------------------------------------------------------------------- |
| `docs/index.html`      | The documentation site: the system, its layers and its design, as pictures. Open it in a browser; there is no build step. |
| `ARCHITECTURE.md`      | The system, how the code is layered, and what every folder is for.    |
| `AGENTS.md`            | Conventions, enforced by hooks and CI. Read before contributing.      |
| `.integrity/POLICY.md` | AI use policy. **Required reading before your first commit.**         |

---

## License

Licensed under the [GNU Affero General Public License v3.0](LICENSE). Every user accepts it
before using the software.

## AI Use Statement

This project uses AI coding assistants, and does so under a written policy:
[`.integrity/POLICY.md`](.integrity/POLICY.md).

- **Tool:** Claude Code, GitHub Copilot CLI, and locally-run open-source models.
- **Mode:** Local.
- **Output:** repository scaffolding, git hooks, CI workflows, agent skills, documentation, and
  drafts of the architecture decision records. Application code as the project proceeds.
- **Data:** none. No sponsor or personal data is placed in prompts; data is described by its
  shape, never its contents. Hosted tooling here is consumer-tier rather than an enterprise
  tenancy, so prompts sent to it are treated as leaving the organisation permanently. Prompts
  to the locally-run models do not leave the machine.
- **Verified:** _[each developer records their own verification per commit; see the AI Use
  Statement in individual commit messages]_

Each commit produced with agent assistance carries its own statement naming the tool, model,
mode, what was generated, and how the developer checked it. Session transcripts are exported to
a team audit log by `scripts/export_ai_audit.py`.

Developers remain the authors of what they commit and are accountable for understanding it.
Agent assistance does not transfer that.

## Reference

> _Policy on the Use of Generative AI._ ENEL 500 — Computer, Electrical, and Software
> Engineering Team Design, Fall 2026. Department of Software and Electrical Engineering,
> University of Calgary. Hamidreza Zareipour. Accessed via D2L.
