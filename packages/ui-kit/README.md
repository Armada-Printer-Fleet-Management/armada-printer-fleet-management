# `packages/ui-kit/` — shared UI components

`@armada/ui-kit` contains presentational React components used by both `apps/web/` and
`apps/desktop/frontend/`. The package is source-first: Vite compiles its TypeScript directly
through the repository workspace rather than requiring a separate package build.

## Component boundaries

Components belong here when they:

- render from props and local composition;
- expose normal HTML attributes and accept a `className` override;
- use only React, the UI-kit utilities, and styling tokens; and
- work in both a browser and the desktop pywebview frontend.

Keep routes, API calls, IPC, application state, and deployment-specific configuration in the
application that owns them. The UI kit must never import from `apps/`, `plugins/`, or
`packages/api-client/`.

## Creating a component

1. Add the component under `src/components/` and follow shadcn/ui's composable component
   pattern when a component has meaningful subparts.
2. Use `React.forwardRef` for DOM-backed components and preserve the corresponding HTML
   attributes in the public props.
3. Combine caller classes with `cn()` from `src/lib/utils.ts`; do not construct Tailwind
   utility names by interpolating partial strings.
4. Use the shared semantic tokens (`bg-card`, `text-card-foreground`, `border`, and related
   variables) instead of hard-coded application colors.
5. Export the component from `src/index.ts` and keep the public API intentionally small.
6. Add or update an application example when the component introduces a new usage pattern.

Tailwind scans source as text. Variant props should map to complete, statically present class
strings so both app builds generate the required CSS. Each app stylesheet registers
`packages/ui-kit/src` with `@source` for this reason.

## Usage

```tsx
import { Card, CardContent, CardHeader, CardTitle } from "@armada/ui-kit";

<Card>
  <CardHeader>
    <CardTitle>Printer fleet</CardTitle>
  </CardHeader>
  <CardContent>Shared content</CardContent>
</Card>;
```

The applications import `@armada/ui-kit/styles.css` after Tailwind and declare the workspace
dependency as `"@armada/ui-kit": "workspace:*"`.

References: [shadcn/ui monorepos](https://ui.shadcn.com/docs/monorepo) and
[Tailwind source detection](https://tailwindcss.com/docs/detecting-classes-in-source-files).
