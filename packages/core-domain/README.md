# `packages/core-domain/` — domain logic

Core business rules live here. Domain driven

**No I/O, no framework imports, no network.** That constraint is what makes it runnable in both
places and testable without fixtures.

If something here looks like it needs a database or an HTTP call, it needs a port in
`packages/plugin-api/` instead.

May not import from `plugin-api/`, `plugins/`, or `apps/`.
