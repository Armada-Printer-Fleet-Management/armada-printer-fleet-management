# Architecture

The shape of the system and the repository: what runs where, how the code is layered, and where
each thing lives. **Read this before planning any change.** The rules that enforce this shape are
in `AGENTS.md`; the human pictures of it are `docs/index.html` and the pages in its Docs map.

## System

Two servers:

- **Application server** (`apps/server`, remote): the only server either client talks to. It
  faces students and operators over the internet and validates every request before anything
  reaches a site.
- **Printer server** (`apps/printer_server`, on-premise, one per print site): the only thing that
  talks to printers. Only the application server talks to it; no client connects to it directly.

```mermaid
flowchart LR
    student(["Student"])
    operator(["Operator"])

    subgraph clients["Clients"]
        web["apps/web<br/>(browser)"]
        desktop["apps/desktop<br/>(operator UI)"]
    end

    subgraph remotetier["Remote / central"]
        remote["apps/server<br/>(application server)"]
    end

    subgraph sitetier["On-premise site"]
        local["apps/printer_server<br/>(printer server)"]
        printers["3D printers"]
    end

    student --> web
    operator --> desktop
    web -->|"submit print job<br/>(ConnectRPC)"| remote
    desktop <-->|"status / control<br/>(ConnectRPC)"| remote
    remote -->|"validated job<br/>(ConnectRPC)"| local
    local -->|"drive & monitor"| printers
``` Which service owns which data, and how a print
flows between them, is `data-management-choices.md`.

## Codebase design

| Layer | Path | Why it's a separate layer |
|---|---|---|
| L0 | `packages/proto/` | The wire contract. Server, web and desktop all agree on message shapes from one source, so they can't silently drift apart. Everything may depend on it; it depends on nothing. |
| L1 | `packages/core-domain/` | Domain logic that is reusable across multiple applications. |
| L2 | `packages/plugin-api/` | The interfaces the core domain needs, with no implementation. |
| L3 | `plugins/*` | The vendor-specific half of the implementation. An adapter translates one external system into the interface the core domain expects. Swapping the vendor means writing or reconfiguring an adapter, never touching the domain. |
| L4 | `apps/*` | The only place allowed to construct a concrete adapter and wire it to a port. A deployment's specific integrations become a matter of _which adapters get constructed_, not a code change. |

A concrete case through those layers: a new deployment switching its identity provider from the
default email-and-password login to an OIDC provider such as Microsoft Entra. Highlighted means it
changes; the rest does not.

```mermaid
flowchart TD
    L4["L4 — apps/*<br/>constructs whichever adapter<br/>is named in config/app.yaml"]
    L3["L3 — plugins/*<br/>the vendor-specific adapter"]
    OLD["default: email + password<br/>(existing plugin)"]
    NEW["new: plugins/auth-oidc<br/>(Microsoft Entra)"]
    L2["L2 — packages/plugin-api<br/>port: verify a credential,<br/>return an identity"]
    L1["L1 — packages/core-domain<br/>sees only 'Operator X,<br/>these roles'"]
    L0["L0 — packages/proto<br/>same login message shape"]

    L4 --> L3
    L3 -.->|"swapped out"| OLD
    L3 -->|"swapped in"| NEW
    L3 --> L2 --> L1 --> L0

    classDef changed fill:#ffe4b0,stroke:#b35900,stroke-width:2px,color:#111;
    classDef removed fill:#f5f5f5,stroke:#999,stroke-dasharray: 4 3,color:#777;
    classDef unchanged fill:#eef,stroke:#556,color:#111;
    class L3,NEW changed;
    class OLD removed;
    class L4,L2,L1,L0 unchanged;
```

Only L3 changes for the switch: `apps/*` already knows how to construct whichever adapter is
named in `config/app.yaml`, so swapping providers means changing that one line, never the port,
the domain or the wire contract. How business logic is shaped inside L1 and the apps is the DDD
section of `AGENTS.md`.

## Folder structure

Each directory below has a `README.md` with its contents, and the ones marked † have their own
`AGENTS.md` with rules that apply only there.

```text
apps/                      L4: the delivered applications
  server/ †                the application server: Python ASGI + ConnectRPC, remote
  web/                     React + TypeScript browser app for students
  desktop/ †               pywebview backend/ around a React frontend/, plus installer/
packages/                  shared code, used by more than one app
  proto/ †                 L0: the .proto contract; utils/ holds the generated Python and mappers
  core-domain/             L1: entities, their rules, typed IDs and DDD bases
  plugin-api/              L2: ports that plugins implement
  organization-info/       the organization's title, description, licence and repository
  ui-kit/                  presentational React components shared by both frontends
  api-client/              generated ConnectRPC client and typed web API
plugins/                   L3: adapters (auth-oidc, identity-local, s3-file-store, theme-default)
infra/
  dev/                     local development stack: server, web, Postgres, Garage, Keycloak
  deploy/                  the stack every deployed machine runs, and its installer and armada command
config/                    deployment configuration; gitignored except *.example.* files
docs/                      human documentation site: why and pictures (see the Docs map)
scripts/                   repository tooling: codegen, agent config sync, audit export, installers
bruno/                     API request collection for trying the server by hand
.claude/skills/            agent skills; the source for the generated .github/skills/ and prompts/
.githooks/                 commit-msg, pre-commit and pre-push enforcement
.github/                   CI workflows and pinned actions
.integrity/                AI use policy and statement format
```

Root files worth knowing: `AGENTS.md` (rules), `data-management-choices.md` (data ownership and
flows), `buf.yaml` and `buf.gen.*.yaml` (codegen templates), `package.json` and
`pnpm-workspace.yaml` (the JS workspace).

---

## AI Use Statement

```text
AI Use Statement
  Tool:     Claude Code (Opus 5.5)
  Mode:     Local
  Output:   moved the system and layer diagrams here from the README, corrected the server
            topology, and added the folder map
  Data:     none
  Verified: Proof read and verified accuracy to current project's progress and standard.
            Applied reformatting to remove bloat documentation.
```
