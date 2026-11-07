#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ "$#" -ne 1 ]]; then
  printf 'Usage: %s IMAGE_TAG\n' "$0" >&2
  exit 2
fi

image_tag="$1"
confirmation_phrase="ROLL BACK OWNER-BETA UAT"
printf 'This deploys the selected older application image without reversing database migrations.\n'
printf 'Confirm schema compatibility and take an approved backup before continuing.\n'
if ! read -r -p "Type \"$confirmation_phrase\" to continue: " confirmation; then
  printf 'Confirmation was not provided; no deployment was changed.\n' >&2
  exit 2
fi
if [[ "$confirmation" != "$confirmation_phrase" ]]; then
  printf 'Confirmation did not match; no deployment was changed.\n' >&2
  exit 2
fi

"$script_dir/deploy-image.sh" --rollback "$image_tag"
