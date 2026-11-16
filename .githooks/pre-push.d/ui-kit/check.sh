# ── UI kit: types, lint and component tests ────────────────────────────────
if [ -f packages/ui-kit/package.json ]; then
  require "ui-kit: tsc" pnpm pnpm --dir packages/ui-kit exec tsc --noEmit
  require "ui-kit: eslint" pnpm pnpm --dir packages/ui-kit exec eslint src --max-warnings=0
  require_exhaustive "ui-kit: vitest" pnpm pnpm --dir packages/ui-kit exec vitest run
else
  NA+=("ui-kit")
fi
