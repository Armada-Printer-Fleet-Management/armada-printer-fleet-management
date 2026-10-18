# ── Deployment scripts (bash) ────────────────────────────────────────────────
if [ -f infra/deploy/armada ]; then
  require "deploy: shellcheck" shellcheck shellcheck infra/deploy/armada infra/deploy/*.sh
else
  NA+=("deploy")
fi
