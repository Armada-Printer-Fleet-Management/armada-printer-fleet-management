red() { printf '\033[31m%s\033[0m\n' "$*"; }
grn() { printf '\033[32m%s\033[0m\n' "$*"; }
dim() { printf '\033[2m%s\033[0m\n' "$*"; }
have() { command -v "$1" >/dev/null 2>&1; }

# Prints the first Python on PATH that actually runs. Windows puts python and
# python3 placeholders on PATH that only point to the Microsoft Store, so the first
# one found is not necessarily a real interpreter.
find_python() {
  local candidate
  while IFS= read -r candidate; do
    if "$candidate" -c "" >/dev/null 2>&1; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done < <(type -ap python3 python)
  return 1
}

run_in() {
  local dir="$1"; shift
  (cd "$dir" && "$@")
}

now() { printf '%s' "${EPOCHREALTIME/,/.}"; }
elapsed() { awk -v a="$1" -v b="$(now)" 'BEGIN { printf "%.1fs", b - a }'; }

# AFFECTED holds the project directories this push changes, one per line, or ALL.
# The dispatcher fills it from scripts/affected_projects.py before any check runs.
AFFECTED="ALL"

# is_affected <dir>: whether checks for the project at <dir> should run. A directory
# that is not a project (no manifest) always counts, so an unknown check is never skipped.
is_affected() {
  local dir="${1%/}"
  dir="${dir%/node_modules}"
  [ "$AFFECTED" = "ALL" ] && return 0
  [ -f "$dir/pyproject.toml" ] || [ -f "$dir/package.json" ] || return 0
  printf '%s\n' "$AFFECTED" | grep -qxF "$dir"
}

# any_affected <dir...>: whether at least one of the given projects is affected.
any_affected() {
  local dir
  for dir in "$@"; do
    is_affected "$dir" && return 0
  done
  return 1
}

# Prints the project a command runs in, taken from `run_in <dir>`, `--dir <dir>`,
# `--project <dir>` or `--node-modules <dir>`, or nothing if it names none.
project_of() {
  local previous=""
  for arg in "$@"; do
    case "$previous" in
      run_in|--dir|--project|--node-modules) printf '%s\n' "$arg"; return ;;
    esac
    previous="$arg"
  done
}

# skip_unchanged <label> <what>: reports a gate skipped because <what> did not change.
skip_unchanged() {
  printf '  %-26s ' "$1"
  dim "skipped (no changes in ${2%/node_modules})"
  SKIPPED_UNCHANGED=$((SKIPPED_UNCHANGED + 1))
}

# require <label> <tool> <command...>
# Runs a mandatory gate. A missing tool is a failure, not a skip. The gate is
# skipped, and says so, when the project it runs in is not affected by this push.
# Mutates the caller's FAILED and counters, so this must be sourced into the
# dispatcher's shell, never executed as a subprocess.
require() {
  local label="$1" tool="$2"; shift 2
  local project start
  project="$(project_of "$@")"
  if [ -n "$project" ] && ! is_affected "$project"; then
    skip_unchanged "$label" "$project"
    return
  fi
  printf '  %-26s ' "$label"
  if ! have "$tool"; then
    red "MISSING"
    dim "    '$tool' is not installed but this repo requires it."
    dim "    Run /onboarding to set up your environment."
    FAILED=1
    return
  fi
  start="$(now)"
  RAN=$((RAN + 1))
  if output=$("$@" 2>&1); then
    grn "ok  $(elapsed "$start")"
  else
    red "FAILED  $(elapsed "$start")"
    printf '%s\n' "$output" | sed 's/^/    /'
    FAILED=1
  fi
}

# require_exhaustive <label> <tool> <command...>
# A gate too slow or environment-heavy for every push (Docker, browser, WASM, long
# suites). CI always runs it; locally it runs only with PRE_PUSH_EXHAUSTIVE=1.
require_exhaustive() {
  if [ "${PRE_PUSH_EXHAUSTIVE:-}" = "1" ]; then
    require "$@"
  else
    printf '  %-26s ' "$1"
    dim "skipped (CI only; PRE_PUSH_EXHAUSTIVE=1 runs it)"
    SKIPPED_CI_ONLY=$((SKIPPED_CI_ONLY + 1))
  fi
}