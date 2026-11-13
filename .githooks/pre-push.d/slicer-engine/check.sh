# ── Slicer engine: the fetched engine matches its pin and loads ─────────────
if [ -f packages/slicer-engine/engine.pin.json ]; then
  require "slicer: pin" python python scripts/fetch_slicer_engine.py --check
  require "slicer: tsc" pnpm pnpm --dir packages/slicer-engine exec tsc --noEmit
  require "slicer: eslint" pnpm pnpm --dir packages/slicer-engine exec eslint src vite.ts --max-warnings=0
  require "slicer: vitest" pnpm pnpm --dir packages/slicer-engine exec vitest run
else
  NA+=("slicer-engine")
fi
