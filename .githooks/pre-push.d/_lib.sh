red() { printf '\033[31m%s\033[0m\n' "$*"; }
grn() { printf '\033[32m%s\033[0m\n' "$*"; }
dim() { printf '\033[2m%s\033[0m\n' "$*"; }
have() { command -v "$1" >/dev/null 2>&1; }

run_in() {
  local dir="$1"; shift
  (cd "$dir" && "$@")
}

# require <label> <tool> <command...>
# Runs a mandatory gate. A missing tool is a failure, not a skip. Mutates the
# caller's FAILED variable, so this must be sourced into the dispatcher's shell,
# never executed as a subprocess.
require() {
  local label="$1" tool="$2"; shift 2
  printf '  %-14s ' "$label"
  if ! have "$tool"; then
    red "MISSING"
    dim "    '$tool' is not installed but this repo requires it."
    dim "    Run /onboarding to set up your environment."
    FAILED=1
    return
  fi
  if output=$("$@" 2>&1); then
    grn "ok"
  else
    red "FAILED"
    printf '%s\n' "$output" | sed 's/^/    /'
    FAILED=1
  fi
}