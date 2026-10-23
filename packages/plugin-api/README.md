# `packages/plugin-api/` — the ports

The interfaces adapters implement: `Protocol` classes in Python, `interface` types in
TypeScript.

A port describes **what the domain needs, in the domain's own words** — not what a particular
vendor happens to offer. Implementations live in `plugins/`, and only `apps/` may construct one.

| Port | Module | What it stores or does | Plugins |
|---|---|---|---|
| `FileStore` | `plugin_api.file_store` | Streams files in and out by key, and deletes them | `s3-file-store` |

A port's errors describe the external system, not the domain. The app's infrastructure adapter
that wraps a port translates them into domain errors, so no domain or handler sees them: a
missing file, for example, becomes `EntityNotFound` for that file's typed ID, and an outage
becomes `Unavailable`.

Changing a port breaks every adapter implementing it, so treat it as a public interface and work
in plan mode.
