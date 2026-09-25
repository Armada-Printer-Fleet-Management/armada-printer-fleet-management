---
name: shadcn-components
description: "Create and update shadcn-inspired React components in the shared @armada/ui-kit package, following its TypeScript, Tailwind CSS, semantic-token, accessibility, and cross-app conventions."
---

# Shared UI components

Use this workflow when creating or changing reusable React UI components for the web and
desktop applications. The canonical package is `packages/ui-kit/` (`@armada/ui-kit`), a
source-first shared package. Follow shadcn/ui's composable component patterns, but adapt them
to this repository rather than introducing a separate component package or copying components
into each application.

Before editing, read `packages/ui-kit/README.md` and inspect nearby components, styles, and
consumers. Keep application routes, API calls, IPC, application state, and deployment
configuration in their owning app. Components in the UI kit must work in both browser and
pywebview frontends and must not import from `apps/`, `plugins/`, or `packages/api-client/`.

## Component implementation

- Put components in `packages/ui-kit/src/components/` and export their public API by name from
  `packages/ui-kit/src/index.ts`.
- Use React and TypeScript with strict types. Preserve the wrapped element's native props,
  including event handlers and accessibility attributes; do not use `any`, unjustified type
  assertions, or unnecessarily narrow callback types.
- Follow the package's DOM-ref convention: use `React.forwardRef` for DOM-backed components,
  type the element and props, and set `displayName`.
- Accept `className` where callers need to customize layout or presentation. Merge it with
  defaults using `cn()` from `packages/ui-kit/src/lib/utils.ts`; do not concatenate class
  strings or dynamically build partial Tailwind utility names.
- Prefer native HTML elements and composition. Use named subcomponents when they make a
  component's structure clearer; avoid adding abstractions for simple markup.
- Keep public props small and behavior predictable. Use controlled/uncontrolled behavior only
  when it is useful to consumers, and do not hide application-specific behavior in a shared
  primitive.
- Keep components declarative: follow the Rules of Hooks, do not mutate props or state, and
  avoid effects for values that can be derived during render.
- Include accessible names, native semantics, keyboard operation, and visible focus states.
  Prefer native element behavior; add ARIA only when it supplies semantics that HTML does not.
- Do not add dependencies just to match an upstream example. First check what the workspace
  already provides; if a new dependency appears necessary, explain its purpose and alternatives
  and get the developer's approval before changing manifests.

## Styling and theme

- Style with Tailwind CSS utility classes. Use the shared `cn()` helper for class composition.
- Prefer the semantic theme utilities already mapped in
  `packages/ui-kit/src/styles.css`, such as `bg-background`, `text-foreground`, `bg-card`,
  `text-card-foreground`, `bg-primary`, `text-primary-foreground`, and `border-border`.
  Check that a token exists before using it.
- Do not hard-code palette colors (for example `text-slate-600` or arbitrary hex values) for
  component states. If a needed semantic role is missing, add a named CSS variable and its
  Tailwind `@theme inline` mapping in the shared stylesheet, with appropriate theme values,
  rather than embedding a one-off color in the component.
- Keep variant classes complete and statically present in source. Tailwind scans source files as
  text, so avoid interpolated fragments such as `bg-${color}-500`. Use a map from each variant
  to its full class string.
- Keep caller overrides last in `cn()` so `tailwind-merge` can resolve conflicting utilities.
  Use arbitrary values only when no existing utility or semantic token expresses the design.
- The apps import `@armada/ui-kit/styles.css` after Tailwind and scan
  `packages/ui-kit/src` with `@source`. Preserve these integrations when changing the package.

## Workflow

1. Confirm the component belongs in the shared UI kit and can remain independent of either app.
2. Check existing components, `cn()`, theme tokens, consuming apps, and the UI-kit README for
   conventions to reuse.
3. Implement the component in `src/components/`, preserving native props, refs, semantic
   styling, accessibility, and static Tailwind classes.
4. Export it from `src/index.ts`. Keep examples in the consuming app when they demonstrate a
   new usage pattern.
5. Run the targeted UI-kit typecheck: `pnpm --filter @armada/ui-kit typecheck`. If behavior or
   styling integration changed, also run the relevant existing app check or test and ensure
   both app stylesheets still include the shared CSS and source paths.

The shadcn CLI is not required for this source-first workflow. Do not add CLI configuration or
change component ownership to make a CLI command work unless the developer explicitly chooses
that workflow.

## References

- [shadcn/ui monorepos](https://ui.shadcn.com/docs/monorepo)
- [shadcn/ui theming](https://ui.shadcn.com/docs/theming)
- [shadcn/ui manual installation](https://ui.shadcn.com/docs/installation/manual)
- [Tailwind CSS source detection](https://tailwindcss.com/docs/detecting-classes-in-source-files)
