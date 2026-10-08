# ── Core domain (Python) ─────────────────────────────────────────────────────
if [ -f packages/core-domain/pyproject.toml ]; then
  require "domain: ruff" uv run_in packages/core-domain uv run ruff check .
  require "domain: pyright" uv run_in packages/core-domain uv run pyright
  require "domain: layers" uv run_in packages/core-domain uv run lint-imports
  require "domain: pytest" uv run_in packages/core-domain uv run pytest -q
else
  NA+=("core-domain")
fi