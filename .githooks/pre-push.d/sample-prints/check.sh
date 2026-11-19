# ── Sample prints: only bundled/ prints ship ───────────────────────────────
if [ -f packages/sample-prints/package.json ]; then
  require "prints: tsc" pnpm pnpm --dir packages/sample-prints exec tsc --noEmit
  require "prints: eslint" pnpm pnpm --dir packages/sample-prints exec eslint src vite.ts --max-warnings=0
  require "prints: vitest" pnpm pnpm --dir packages/sample-prints exec vitest run
else
  NA+=("sample-prints")
fi
