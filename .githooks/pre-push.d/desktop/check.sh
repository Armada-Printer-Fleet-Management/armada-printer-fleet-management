# ── Desktop: backend (Python) ───────────────────────────────────────────────
if [ -f apps/desktop/backend/pyproject.toml ]; then
  require "backend: generate" buf python scripts/generate_proto.py buf.gen.python.yaml
  require "backend: ruff" uv run_in apps/desktop/backend uv run ruff check .
  require "backend: pyright" uv run_in apps/desktop/backend uv run pyright
else
  NA+=("desktop-backend")
fi

# ── Desktop: frontend (TypeScript) ──────────────────────────────────────────
if [ -f apps/desktop/frontend/package.json ]; then
  if [ ! -d apps/desktop/frontend/node_modules ]; then
    printf '  %-14s ' "desktop-frontend"
    red "MISSING"
    dim "    Dependencies are not installed. Run 'pnpm install' in apps/desktop/frontend or /onboarding."
    FAILED=1
  else
    require "frontend: generate" buf bash -c \
      'PATH="$(pwd)/apps/desktop/frontend/node_modules/.bin:$PATH" python scripts/generate_proto.py buf.gen.ts.yaml --node-modules apps/desktop/frontend/node_modules'
    require "frontend: tsc" pnpm pnpm --dir apps/desktop/frontend exec tsc --noEmit
    require "frontend: eslint" pnpm pnpm --dir apps/desktop/frontend exec eslint .
  fi
else
  NA+=("desktop-frontend")
fi