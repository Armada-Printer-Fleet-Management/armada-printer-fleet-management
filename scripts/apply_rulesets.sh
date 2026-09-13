#!/usr/bin/env bash
# Create or update this project's branch and tag rulesets.
#
#   scripts/apply_rulesets.sh <org>          apply across the organisation
#   scripts/apply_rulesets.sh <org>/<repo>   apply to one repository
#
# Organisation-wide rulesets over private repositories need a Team plan or above.
# On a free organisation, pass <org>/<repo> instead.
#
# Requires the gh CLI, authenticated with admin rights. Re-running updates in place.
set -euo pipefail

TARGET="${1:-}"
if [ -z "$TARGET" ]; then
  echo "usage: $0 <org> | <org>/<repo>" >&2
  exit 2
fi

if [[ "$TARGET" == */* ]]; then
  SCOPE="/repos/${TARGET}/rulesets"
  CONDITION_EXTRA=""
  echo "Applying rulesets to repository ${TARGET}"
else
  SCOPE="/orgs/${TARGET}/rulesets"
  CONDITION_EXTRA=', "repository_name": { "include": ["~ALL"], "exclude": [] }'
  echo "Applying rulesets across organisation ${TARGET}"
fi

# A skipped job reports no status, so requiring one that has never run leaves
# pull requests pending forever. Add python, typescript and proto here once each
# has reported on a real pull request.
REQUIRED_CHECKS='
  { "context": "gitleaks" },
  { "context": "commit-messages" }
'

# Linear history is intentionally not enforced, so merge commits stay possible
# for the cases that need them. Rebase is the norm, upheld in review.
branch_rules() {
  cat <<JSON
  { "type": "deletion" },
  { "type": "non_fast_forward" },
  {
    "type": "pull_request",
    "parameters": {
      "required_approving_review_count": 1,
      "dismiss_stale_reviews_on_push": true,
      "require_code_owner_review": false,
      "require_last_push_approval": false,
      "required_review_thread_resolution": true,
      "allowed_merge_methods": ["rebase", "merge"]
    }
  },
  {
    "type": "required_status_checks",
    "parameters": {
      "strict_required_status_checks_policy": true,
      "do_not_enforce_on_create": false,
      "required_status_checks": [ ${REQUIRED_CHECKS} ]
    }
  }
JSON
}

ruleset_json() {
  local name="$1" target="$2" refs="$3" rules="$4"
  cat <<JSON
{
  "name": "${name}",
  "target": "${target}",
  "enforcement": "active",
  "bypass_actors": [],
  "conditions": {
    "ref_name": { "include": [${refs}], "exclude": [] }${CONDITION_EXTRA}
  },
  "rules": [ ${rules} ]
}
JSON
}

apply() {
  local name="$1" body="$2" id
  id=$(gh api "$SCOPE" --jq ".[] | select(.name==\"${name}\") | .id" 2>/dev/null | head -1)
  if [ -n "$id" ]; then
    printf '%s' "$body" | gh api --method PUT "${SCOPE}/${id}" --input - >/dev/null
    echo "  updated  ${name}"
  else
    printf '%s' "$body" | gh api --method POST "$SCOPE" --input - >/dev/null
    echo "  created  ${name}"
  fi
}

apply "main" "$(ruleset_json "main" "branch" '"~DEFAULT_BRANCH"' "$(branch_rules)")"
apply "release" "$(ruleset_json "release" "branch" '"refs/heads/release/**"' "$(branch_rules)")"
apply "version-tags" "$(ruleset_json "version-tags" "tag" '"refs/tags/v*"' \
  '{ "type": "deletion" }, { "type": "non_fast_forward" }, { "type": "update" }')"

echo "Done. Review at: https://github.com/${TARGET%%/*}/settings/rules"
