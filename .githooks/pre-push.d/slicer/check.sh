# ── Slicer: generated code, types, lint and tests ───────────────────────────
if [ -f packages/slicer/package.json ]; then
  require "slicer: generate" buf bash -c \
    'PATH="$(pwd)/packages/slicer/node_modules/.bin:$PATH" python scripts/generate_proto.py buf.gen.slicer_ts.yaml --node-modules packages/slicer/node_modules'
  require "slicer: tsc" pnpm pnpm --dir packages/slicer exec tsc --noEmit
  require "slicer: eslint" pnpm pnpm --dir packages/slicer exec eslint src scripts --max-warnings=0
  require "slicer: vitest" pnpm pnpm --dir packages/slicer exec vitest run
else
  NA+=("slicer")
fi
