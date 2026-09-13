# `packages/` — shared libraries

Code shared by more than one application.

| Directory | What it is |
|---|---|
| `proto/` | The `.proto` API contract |
| `core-domain/` | Domain logic, with no I/O and no framework |
| `plugin-api/` | The ports that adapters implement |
| `ui-kit/` | Presentational React components, shared by both frontends |
| `api-client/` | Generated ConnectRPC client, shared by both frontends |

**Dependencies point inward only**, and `import-linter` fails the build on a violation. Nothing
here may import from `plugins/` or `apps/`.
