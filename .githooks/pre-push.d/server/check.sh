# ── Server (Python) ──────────────────────────────────────────────────────────
if [ -f apps/server/pyproject.toml ]; then
  require "server: ruff" uv run_in apps/server uv run ruff check .
else
  NA+=("server")
fi
