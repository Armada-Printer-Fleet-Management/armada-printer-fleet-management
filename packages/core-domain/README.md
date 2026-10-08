# `packages/core-domain/` — domain logic

Core business rules live here, shared by every Python app.

| Path | Holds |
|---|---|
| `core_domain/ddd/` | Generic bases: `TypedId`, `Entity`, repository ports, `Service`, `change()`, domain errors |
| `core_domain/ids/` | The ID kernel, one file per domain, mirroring `packages/proto/id/v1/` |
| `core_domain/<domain>/` | `entities.py`: the entity and its rules, defined once |

Each app's own domain services and repositories build on these; see the DDD section of the root
`AGENTS.md` and `docs/domain-architecture.html`.

**No I/O, no framework imports, no network.** That constraint is what makes it runnable in both
places and testable without fixtures.

If something here looks like it needs a database or an HTTP call, it needs a port in
`packages/plugin-api/` instead.

May not import from `plugin-api/`, `plugins/`, or `apps/`.
