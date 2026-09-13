# `packages/proto/` — the API contract

The `.proto` files defining every service and message that crosses a process boundary.

**No dependencies.** This is the root of the dependency graph: everything may depend on it, and
it depends on nothing.

`buf generate` produces the Python server interfaces and TypeScript clients from here into
`**/gen/`, which is gitignored and never hand-edited.

Changing a message shape changes both applications at once. Treat it as a public interface.
