# ── UI tests: the shared browser-test harness and the ui-kit kitchen sink ────
if [ -f packages/ui-tests/package.json ]; then
  require "ui-tests: tsc" pnpm pnpm --dir packages/ui-tests exec tsc --noEmit
  require "ui-tests: eslint" pnpm pnpm --dir packages/ui-tests exec eslint src kitchen-sink e2e playwright.config.ts --max-warnings=0
  # Needs Chromium (playwright install chromium) and starts the kitchen sink's dev server.
  require_exhaustive "ui-tests: playwright" pnpm pnpm --dir packages/ui-tests exec playwright test
else
  NA+=("ui-tests")
fi
