#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "$script_dir/../../.." && pwd)"
command -v aws >/dev/null
command -v docker >/dev/null
command -v git >/dev/null
source "$script_dir/deployment-output.sh"

initialize_ledger=false
if [[ "${1:-}" == "--initialize-ledger" ]]; then
  initialize_ledger=true
  shift
fi
if [[ "$#" -ne 0 ]]; then
  printf 'Usage: %s [--initialize-ledger]\n' "$0" >&2
  exit 2
fi

if [[ -n "$(git -C "$repo_root" status --porcelain --untracked-files=normal)" ]]; then
  printf 'Refusing to deploy from a dirty working tree; commit or remove local changes first.\n' >&2
  exit 1
fi

commit="$(git -C "$repo_root" rev-parse --verify HEAD)"
image_tag="${commit:0:12}-$(date -u '+%Y%m%d%H%M%S%N')"
region="${AWS_REGION:-$(deployment_output aws_region)}"
account_id="$(deployment_output aws_account_id)"
repository="$(deployment_output ecr_repository_url)"
caller_account="$(aws sts get-caller-identity --query Account --output text)"

if [[ "$caller_account" != "$account_id" ]]; then
  printf 'AWS caller account does not match the Terraform deployment account.\n' >&2
  exit 1
fi

aws ecr get-login-password --region "$region" |
  docker login --username AWS --password-stdin "$account_id.dkr.ecr.$region.amazonaws.com"
docker build --tag "$repository:$image_tag" "$repo_root"
docker push "$repository:$image_tag"

if [[ "$initialize_ledger" == true ]]; then
  "$script_dir/deploy-image.sh" --initialize-ledger "$image_tag"
else
  "$script_dir/deploy-image.sh" "$image_tag"
fi
