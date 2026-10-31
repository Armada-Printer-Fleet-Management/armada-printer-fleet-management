# ── DDD review verdict (/pr-ddd) ─────────────────────────────────────────────
# Reads the stored verdict for HEAD's tree; it never runs the review, so it costs no tokens.
# FAILED and NA belong to .githooks/pre-push, which sources this file.
# shellcheck disable=SC2034
if [ -f scripts/ddd_verdict.py ]; then
  PY=$(command -v python3 || command -v python || true)
  printf '  %-14s ' "ddd: verdict"
  if [ -z "$PY" ]; then
    red "MISSING"
    dim "    Python is not installed but this repo requires it."
    dim "    Run /onboarding to set up your environment."
    FAILED=1
  elif output=$("$PY" scripts/ddd_verdict.py check 2>&1); then
    grn "ok"
    printf '%s\n' "$output" | sed 's/^/    /'
  else
    red "FAILED"
    printf '%s\n' "$output" | sed 's/^/    /'
    FAILED=1
  fi
else
  NA+=("ddd verdict")
fi
