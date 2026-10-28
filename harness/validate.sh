#!/usr/bin/env bash

set -uo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
LOG_FILE="$ROOT_DIR/interactions/00-initialization/response-00-init.md"
OUTPUT_FILE="$(mktemp)" || {
  printf 'ERROR: could not create temporary output file.\n' >&2
  exit 1
}
STARTED_AT="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

if ! mkdir -p -- "$(dirname -- "$LOG_FILE")"; then
  printf 'ERROR: could not create the interaction log directory.\n' >&2
  rm -f -- "$OUTPUT_FILE"
  exit 1
fi

cleanup() {
  rm -f -- "$OUTPUT_FILE"
}
trap cleanup EXIT

check_directory() {
  local path="$1"
  if [[ -d "$ROOT_DIR/$path" ]]; then
    printf 'PASS: directory exists: %s\n' "$path"
  else
    printf 'FAIL: directory is missing: %s\n' "$path"
    return 1
  fi
}

check_file() {
  local path="$1"
  if [[ -f "$ROOT_DIR/$path" ]]; then
    printf 'PASS: file exists: %s\n' "$path"
  else
    printf 'FAIL: file is missing: %s\n' "$path"
    return 1
  fi
}

validate_repository() {
  local failures=0

  check_directory "specs" || failures=$((failures + 1))
  check_directory "harness" || failures=$((failures + 1))
  check_directory "interactions" || failures=$((failures + 1))
  check_file ".cursorrules" || failures=$((failures + 1))
  check_file "harness/validate.sh" || failures=$((failures + 1))
  check_file "specs/00-initialization/spec-00-init.md" || failures=$((failures + 1))

  if (( failures > 0 )); then
    printf 'Validation failed with %d missing requirement(s).\n' "$failures"
    return 1
  fi

  printf 'Baseline repository validation passed.\n'
}

execute() {
  validate_repository || return $?

  if (( $# == 0 )); then
    return 0
  fi

  if [[ "$1" == "--" ]]; then
    shift
  fi
  if (( $# == 0 )); then
    printf 'ERROR: provide a command after --.\n'
    return 2
  fi

  printf 'Running requested command.\n'
  "$@"
}

{
  execute "$@"
} 2>&1 | tee "$OUTPUT_FILE"
STATUS=${PIPESTATUS[0]}

if ! {
  printf '\n## Execution - %s\n\n' "$STARTED_AT"
  printf -- '- Invocation: `bash harness/validate.sh'
  if (( $# > 0 )); then
    printf ' %q' "$@"
  fi
  printf '`\n- Exit status: `%s`\n\n' "$STATUS"
  printf '### Output\n\n```text\n'
  cat -- "$OUTPUT_FILE"
  printf '```\n'
} >> "$LOG_FILE"; then
  printf 'ERROR: could not append execution results to %s\n' "$LOG_FILE" >&2
  exit 1
fi

exit "$STATUS"
