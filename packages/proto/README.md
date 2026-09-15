# `packages/proto/` — the API contract

The `.proto` files defining every service and message that crosses a process boundary.

**No dependencies.** This is the root of the dependency graph: everything may depend on it, and
it depends on nothing.

`buf generate` produces the Python server interfaces and TypeScript clients from here into
`**/gen/`, which is gitignored and never hand-edited.

`utils/` is the one hand-written exception: small helpers for working with the generated code
(e.g. a `MessageToDict` wrapper that doesn't silently drop zero-valued fields) that every
consuming app depends on as a local path dependency, since apps don't share a root workspace.

Changing a message shape changes both applications at once. Treat it as a public interface.
