#!/usr/bin/env bash

set -uo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
INTERACTION_CAPTURE="${INTERACTION_CAPTURE:-0}"
if [[ "$INTERACTION_CAPTURE" != "0" && "$INTERACTION_CAPTURE" != "1" ]]; then
  printf 'ERROR: INTERACTION_CAPTURE must be 0 or 1.\n' >&2
  exit 2
fi

if [[ "$INTERACTION_CAPTURE" == "1" ]]; then
  if [[ -z "${INTERACTION_PROMPT:-}" ]]; then
    printf 'ERROR: set INTERACTION_PROMPT when INTERACTION_CAPTURE=1.\n' >&2
    exit 2
  fi
  LOG_PATH="${INTERACTION_LOG:-interactions/00-initialization/response-00-init.md}"
  if [[ "$LOG_PATH" = /* ]]; then
    LOG_FILE="$LOG_PATH"
  else
    LOG_FILE="$ROOT_DIR/$LOG_PATH"
  fi
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
fi

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
  check_directory "src/app" || failures=$((failures + 1))
  check_directory "tests" || failures=$((failures + 1))
  check_file ".cursorrules" || failures=$((failures + 1))
  check_file "harness/validate.sh" || failures=$((failures + 1))
  check_file "specs/00-initialization/spec-00-init.md" || failures=$((failures + 1))
  check_file "specs/01-tech-stack-override/01-tech-stack-override.md" || failures=$((failures + 1))
  check_file "pyproject.toml" || failures=$((failures + 1))
  check_file "Dockerfile" || failures=$((failures + 1))
  check_file "docker-compose.yml" || failures=$((failures + 1))
  check_file "alembic.ini" || failures=$((failures + 1))
  check_file "migrations/versions/0001_initial_schema.py" || failures=$((failures + 1))
  check_file "src/app/main.py" || failures=$((failures + 1))
  check_file "src/app/documents.py" || failures=$((failures + 1))
  check_file "src/app/storage.py" || failures=$((failures + 1))

  if bash -n "$ROOT_DIR/harness/validate.sh"; then
    printf 'PASS: validation harness shell syntax.\n'
  else
    printf 'FAIL: validation harness shell syntax.\n'
    failures=$((failures + 1))
  fi

  if python3 -m compileall -q "$ROOT_DIR/src" "$ROOT_DIR/tests" "$ROOT_DIR/migrations"; then
    printf 'PASS: Python source compiles.\n'
  else
    printf 'FAIL: Python source compilation failed.\n'
    failures=$((failures + 1))
  fi

  if (cd "$ROOT_DIR" && PYTHONPATH="$ROOT_DIR/src" python3 -m unittest discover -s tests -v); then
    printf 'PASS: Python unit tests passed.\n'
  else
    printf 'FAIL: Python unit tests failed.\n'
    failures=$((failures + 1))
  fi

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

if [[ "$INTERACTION_CAPTURE" == "1" ]]; then
  {
    execute "$@"
  } 2>&1 | tee "$OUTPUT_FILE"
  STATUS=${PIPESTATUS[0]}

  if ! {
    printf '\n## Prompt - %s\n\n' "$STARTED_AT"
    printf '### Exact user prompt\n\n````text\n%s\n````\n\n' "$INTERACTION_PROMPT"
    printf '### Execution - %s\n\n' "$STARTED_AT"
    printf -- '- Invocation: `INTERACTION_CAPTURE=1 '
    if [[ -n "${INTERACTION_LOG:-}" ]]; then
      printf 'INTERACTION_LOG=%q ' "$INTERACTION_LOG"
    fi
    printf 'bash harness/validate.sh'
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
fi

execute "$@"
