# `packages/plugin-api/` — the ports

The interfaces adapters implement: `Protocol` classes in Python, `interface` types in
TypeScript.

A port describes **what the domain needs, in the domain's own words** — not what a particular
vendor happens to offer. Implementations live in `plugins/`, and only `apps/` may construct one.

| Port | Module | What it stores or does | Plugins |
|---|---|---|---|
| `FileStore` | `plugin_api.file_store` | Reads, writes and deletes files by key | `s3-file-store` |

A port's errors describe the external system, not the domain. A domain service that uses a port
translates them into domain errors where it can; a missing file, for example, becomes
`EntityNotFound` for that file's typed ID.

Changing a port breaks every adapter implementing it, so treat it as a public interface and work
in plan mode.
