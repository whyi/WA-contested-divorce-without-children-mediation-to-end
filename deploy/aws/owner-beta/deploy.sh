#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "$script_dir/../../.." && pwd)"
command -v aws >/dev/null
command -v docker >/dev/null
command -v terraform >/dev/null
command -v python3 >/dev/null

initialize_ledger=false
if [[ "${1:-}" == "--initialize-ledger" ]]; then
  initialize_ledger=true
  shift
fi
if [[ "$#" -ne 0 ]]; then
  printf 'Usage: %s [--initialize-ledger]\n' "$0" >&2
  exit 2
fi

region="${AWS_REGION:-$(terraform -chdir="$script_dir" output -raw aws_region)}"
account_id="$(terraform -chdir="$script_dir" output -raw aws_account_id)"
repository="$(terraform -chdir="$script_dir" output -raw ecr_repository_url)"
cluster="$(terraform -chdir="$script_dir" output -raw ecs_cluster_name)"
service="$(terraform -chdir="$script_dir" output -raw ecs_service_name)"
bootstrap_task="$(terraform -chdir="$script_dir" output -raw bootstrap_task_definition_arn)"
subnets="$(terraform -chdir="$script_dir" output -raw public_subnet_ids)"
security_group="$(terraform -chdir="$script_dir" output -raw app_security_group_id)"
caller_account="$(aws sts get-caller-identity --query Account --output text)"

if [[ "$caller_account" != "$account_id" ]]; then
  printf 'AWS caller account does not match the Terraform deployment account.\n' >&2
  exit 1
fi

aws ecr get-login-password --region "$region" |
  docker login --username AWS --password-stdin "$account_id.dkr.ecr.$region.amazonaws.com"
docker build --tag "$repository:latest" "$repo_root"
docker push "$repository:latest"

run_bootstrap_task() {
  local task_arn
  local exit_code
  local overrides

  overrides="$(python3 - "$@" <<'PY'
import json
import sys

print(json.dumps({
    "containerOverrides": [{
        "name": "bootstrap",
        "command": sys.argv[1:],
    }]
}))
PY
)"
  task_arn="$(aws ecs run-task \
    --region "$region" \
    --cluster "$cluster" \
    --task-definition "$bootstrap_task" \
    --launch-type FARGATE \
    --network-configuration \
      "awsvpcConfiguration={subnets=[$subnets],securityGroups=[$security_group],assignPublicIp=ENABLED}" \
    --overrides "$overrides" \
    --query 'tasks[0].taskArn' \
    --output text)"

  if [[ -z "$task_arn" || "$task_arn" == "None" ]]; then
    printf 'Could not start the UAT bootstrap task.\n' >&2
    exit 1
  fi

  aws ecs wait tasks-stopped --region "$region" --cluster "$cluster" --tasks "$task_arn"
  exit_code="$(aws ecs describe-tasks \
    --region "$region" \
    --cluster "$cluster" \
    --tasks "$task_arn" \
    --query 'tasks[0].containers[?name==`bootstrap`].exitCode | [0]' \
    --output text)"
  if [[ "$exit_code" != "0" ]]; then
    printf 'UAT bootstrap task failed; inspect its redacted CloudWatch logs.\n' >&2
    exit 1
  fi
}

run_bootstrap_task alembic upgrade head
if [[ "$initialize_ledger" == true ]]; then
  run_bootstrap_task python -m app.deletion_ledger initialize
fi

aws ecs update-service \
  --region "$region" \
  --cluster "$cluster" \
  --service "$service" \
  --desired-count 1 \
  --force-new-deployment >/dev/null
aws ecs wait services-stable --region "$region" --cluster "$cluster" --services "$service"

printf 'Owner-beta UAT deployment is ready for configuration verification at: %s\n' \
  "$(terraform -chdir="$script_dir" output -raw uat_url)"
