# ── Plugin ports and plugins (Python) ───────────────────────────────────────
for project in packages/plugin-api plugins/*/; do
  project="${project%/}"
  [ -f "$project/pyproject.toml" ] || continue
  name="${project##*/}"
  require "$name: ruff" uv run_in "$project" uv run ruff check .
  require "$name: pyright" uv run_in "$project" uv run pyright
  require "$name: pytest" uv run_in "$project" uv run pytest -q
done
