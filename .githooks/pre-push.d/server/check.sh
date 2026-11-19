# ── Server (Python) ──────────────────────────────────────────────────────────
if [ -f apps/server/pyproject.toml ]; then
  require "server: generate" uv uv run --project apps/server python scripts/generate_proto.py buf.gen.server.yaml
  require "server: ruff" uv run_in apps/server uv run ruff check .
  require "server: pyright" uv run_in apps/server uv run pyright
  require "server: layers" uv run_in apps/server uv run lint-imports
  require "server: unit tests" uv run_in apps/server uv run pytest tests/unit -q
  # The integration tests start their own stack, so Docker is required when they run.
  require_exhaustive "server: integration tests" docker run_in apps/server uv run pytest tests/integration -q
else
  NA+=("server")
fi
