# Agent Instructions: `packages/ui-tests/`

The root `AGENTS.md` applies in full. This package is the shared harness for Playwright browser
tests: what Vitest's jsdom cannot see, because it needs a real browser to draw the page. It holds
only what is generic. **Each app owns its own browser tests**, in its `e2e/` folder, and builds on
this package; this package never depends on an app.

## What is here

- `src/`, exported as `@armada/ui-tests`. Use these before writing new helpers.
  - `theme.ts`: `openPage()` (sets the OS theme, turns off motion), and token names and values
    read from ui-kit's theme files, never copied.
  - `axe.ts`: `expectWcagAA()`, and `contrastFailures()` for one element in its current state.
  - `page-checks.ts`: in-page checks that report one plain line per problem: only token colours
    drawn, overflowing content, layout and scrolling problems, console errors and failed requests.
  - `focus.ts`: `tabThrough()` visits every keyboard stop once.
  - `limits.ts`: the measured values the checks share, each with its reason.
- `src/playwright-config.ts`, exported as `@armada/ui-tests/playwright-config`:
  `browserTestConfig({ port, command })`, the settings every suite shares.
- `kitchen-sink/` and `e2e/`: ui-kit's own browser tests. The kitchen sink is a test-only page
  that renders every ui-kit component in its common states. `?theme=light|dark|system` sets the
  start theme; `?dialog=<name>` opens one modal dialog over it.

## Adding browser tests to an app

1. Add `@armada/ui-tests` (`workspace:*`) and `@playwright/test` (the version this package
   pins) to the app's devDependencies, and a `test:browser` script running `playwright test`.
2. Write `playwright.config.ts` calling `browserTestConfig()` with a free port and the command
   that starts the app's dev server. `apps/web/playwright.config.ts` is the example.
3. Put the tests in `e2e/*.e2e.ts`. The `.e2e.ts` name keeps them out of Vitest.
4. Add the suite to the app's pre-push check with `require_exhaustive`, and as a step in CI.

## Rules

- **A new ui-kit component goes on the kitchen sink** in each state it can be in, so every check
  covers it without a new test. A component that needs a modal goes behind `?dialog=`.
- Checks are broad: they run over the whole page. Prefer extending a check in `src/` over a test
  for one element. Nothing app-specific goes in `src/`.
- Tests read token values from `packages/ui-kit/src/theme/`; never hard-code a colour.
- When a check is changed, prove it still fails on a planted bug before relying on it.

## Commands

| Task | Command |
| --- | --- |
| Install the browser (once per machine) | `pnpm --dir packages/ui-tests exec playwright install chromium` |
| Run ui-kit's browser tests | `pnpm --dir packages/ui-tests test:browser` |
| Run an app's browser tests | `pnpm --dir apps/web test:browser` |
| Open the kitchen sink | `pnpm --dir packages/ui-tests kitchen-sink` |
| Read a failure | `pnpm --dir <package> exec playwright show-report` |

Pre-push: `.githooks/pre-push.d/ui-tests/check.sh` (types and lint on every push) and each app's
own check; the browser suites run only in CI or with `PRE_PUSH_EXHAUSTIVE=1`. CI runs them in the
`typescript` job of `.github/workflows/ci.yml`.
