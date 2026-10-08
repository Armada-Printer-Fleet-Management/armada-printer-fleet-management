# ── Server (Python) ──────────────────────────────────────────────────────────
if [ -f apps/server/pyproject.toml ]; then
  require "server: ruff" uv run_in apps/server uv run ruff check .
  require "server: pyright" uv run_in apps/server uv run pyright
  require "server: layers" uv run_in apps/server uv run lint-imports
  require "server: pytest" uv run_in apps/server uv run pytest -q
else
  NA+=("server")
fi
