# `packages/plugin-api/` — the ports

The interfaces adapters implement: `Protocol` classes in Python, `interface` types in
TypeScript.

A port describes **what the domain needs, in the domain's own words** — not what a particular
vendor happens to offer. Implementations live in `plugins/`, and only `apps/` may construct one.

Changing a port breaks every adapter implementing it, so treat it as a public interface and work
in plan mode.
