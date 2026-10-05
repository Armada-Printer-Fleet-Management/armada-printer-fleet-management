# `packages/proto/` — the API contract

The `.proto` files defining every service and message that crosses a process boundary.

**No dependencies.** This is the root of the dependency graph: everything may depend on it, and
it depends on nothing.

`buf generate` produces the Python server interfaces and TypeScript clients from here into
`**/gen/`, which is gitignored and never hand-edited.

`utils/` is the one hand-written exception: small helpers for working with the generated code
(e.g. a `MessageToDict` wrapper that doesn't silently drop zero-valued fields) that every
consuming app depends on as a local path dependency, since apps don't share a root workspace.
Its tests also check the contract's typed-ID rules.

Changing a message shape changes both applications at once. Treat it as a public interface.

## Domain-driven layout

The contract is split along the same domains as the rest of the system
(`data-management-choices.md`). Each domain is its own package, and domains refer to each other
only through typed IDs:

```
            id.v1   (one typed ID per entity: UserId, FileId, PrintJobId, ...)
          common.v1 (base units: TimeStatus, PageRequest, PageResponse)
              ▲
   ┌──────────┼───────────┬─────────────┐
 user.v1   file.v1   print_job.v1   printer.v1      domains: entities, enums
   ▲          ▲           ▲             ▲           (never import each other)
   └──────────┴─────┬─────┴─────────────┘
                    │
      server.v1             printer_server.v1       servers: services and RPCs,
   (remote server)      (on-premise printer server)  composing domains into responses
                    │
                    ▼
        generated Python and TypeScript clients
```

**Why typed IDs.** A bare string can hold any entity's ID, so mixing up a printer's ID and a
job's ID compiles and fails at runtime. Giving each entity its own ID type (`id.v1.PrinterId`,
`id.v1.PrintJobId`) turns that mistake into a build error in every generated client.

The full rules (naming, enums, base units, upload and transition patterns) are in
[`AGENTS.md`](AGENTS.md).
