# `packages/ui-kit/` — shared UI components

Presentational React components used by both `apps/web/` and `apps/desktop/frontend/`. This is
how the two frontends look alike without importing each other.

**Belongs here:** components that render from their props and hold no application state, plus
the design tokens they draw on.

**Does not belong here:** routing, data fetching, or anything that knows which application it is
running inside.

Whether this is built on a component library or from scratch is still an open question.
