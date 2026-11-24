# ── UI kit: types, lint and component tests ────────────────────────────────
if [ -f packages/ui-kit/package.json ]; then
  require "ui-kit: tsc" pnpm pnpm --dir packages/ui-kit exec tsc --noEmit
  require "ui-kit: eslint" pnpm pnpm --dir packages/ui-kit exec eslint src --max-warnings=0
  require_exhaustive "ui-kit: vitest" pnpm pnpm --dir packages/ui-kit exec vitest run
  # Scans every frontend, not just ui-kit, so it runs on every push; it takes under a second.
  require "ui: WCAG" "${PY:-python}" "${PY:-python}" scripts/check_ui_theme.py
else
  NA+=("ui-kit")
fi
