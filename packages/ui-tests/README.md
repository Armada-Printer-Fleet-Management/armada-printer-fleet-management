# UI tests

The shared harness for Playwright browser tests, plus ui-kit's own browser tests. It checks what
is actually drawn: WCAG contrast with axe, theme switching, colours, overflow, focus and page
layout. Each app keeps its own browser tests in its `e2e/` folder and builds on this package.

```bash
pnpm --dir packages/ui-tests exec playwright install chromium   # once per machine
pnpm --dir packages/ui-tests test:browser                       # ui-kit's kitchen sink
pnpm --dir apps/web test:browser                                # the web app
```

The kitchen sink, a page showing every ui-kit component, opens with
`pnpm --dir packages/ui-tests kitchen-sink`.

Rules for agents and contributors: [`AGENTS.md`](AGENTS.md).
