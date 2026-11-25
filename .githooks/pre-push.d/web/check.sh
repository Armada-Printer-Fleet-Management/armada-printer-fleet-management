# ── Web app: the Playwright browser suite ───────────────────────────────────
if [ -f apps/web/package.json ]; then
  # Needs Chromium (playwright install chromium) and starts the web app's dev server.
  require_exhaustive "web: playwright" pnpm pnpm --dir apps/web exec playwright test
else
  NA+=("web")
fi
