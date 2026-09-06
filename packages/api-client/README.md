# `packages/api-client/` — the API client

The TypeScript ConnectRPC client generated from `packages/proto/`, plus the thin hand-written
wrapper both frontends call.

Generated output lives in `gen/`, which is gitignored. Run `buf generate`; never hand-edit it.

**Belongs here:** client construction, transport configuration, and shared error mapping.

**Does not belong here:** React hooks or component state.
