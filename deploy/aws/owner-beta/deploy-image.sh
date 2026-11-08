#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

initialize_ledger=false
rollback=false
if [[ "${1:-}" == "--initialize-ledger" ]]; then
  initialize_ledger=true
  shift
elif [[ "${1:-}" == "--rollback" ]]; then
  rollback=true
  shift
fi
if [[ "$#" -ne 1 || ! "$1" =~ ^[a-zA-Z0-9][a-zA-Z0-9._-]{0,127}$ ]]; then
  printf 'Usage: %s [--initialize-ledger | --rollback] IMAGE_TAG\n' "$0" >&2
  exit 2
fi
if [[ "$rollback" == true && "$initialize_ledger" == true ]]; then
  printf 'Ledger initialization is not allowed during rollback.\n' >&2
  exit 2
fi
image_tag="$1"

command -v aws >/dev/null
command -v python3 >/dev/null
source "$script_dir/deployment-output.sh"

region="${AWS_REGION:-$(deployment_output aws_region)}"
account_id="$(deployment_output aws_account_id)"
repository="$(deployment_output ecr_repository_url)"
cluster="$(deployment_output ecs_cluster_name)"
service="$(deployment_output ecs_service_name)"
app_task_base="$(deployment_output app_task_definition_arn)"
bootstrap_task_base="$(deployment_output bootstrap_task_definition_arn)"
subnets="$(deployment_output public_subnet_ids)"
security_group="$(deployment_output app_security_group_id)"
caller_account="$(aws sts get-caller-identity --query Account --output text)"

if [[ "$caller_account" != "$account_id" ]]; then
  printf 'AWS caller account does not match the Terraform deployment account.\n' >&2
  exit 1
fi

repository_name="${repository##*/}"
image_digest="$(aws ecr describe-images \
  --region "$region" \
  --repository-name "$repository_name" \
  --image-ids "imageTag=$image_tag" \
  --query 'imageDetails[0].imageDigest' \
  --output text)"
if [[ -z "$image_digest" || "$image_digest" == "None" ]]; then
  printf 'The requested immutable image tag does not exist in the UAT ECR repository.\n' >&2
  exit 1
fi

temporary_directory="$(mktemp -d)"
chmod 700 "$temporary_directory"
trap 'rm -rf -- "$temporary_directory"' EXIT

register_task_definition() {
  local source_arn="$1"
  local target_file="$2"
  local image_name="$3"
  local task_definition

  task_definition="$temporary_directory/source-task-definition.json"
  aws ecs describe-task-definition \
    --region "$region" \
    --task-definition "$source_arn" \
    --query taskDefinition \
    --output json >"$task_definition"
  python3 "$script_dir/task_definition.py" \
    "$task_definition" \
    "$target_file" \
    "$repository:$image_tag" \
    "$image_name"
  aws ecs register-task-definition \
    --region "$region" \
    --cli-input-json "file://$target_file" \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text
}

app_task_definition="$(register_task_definition \
  "$app_task_base" \
  "$temporary_directory/app-task-definition.json" \
  api)"
bootstrap_task_definition="$(register_task_definition \
  "$bootstrap_task_base" \
  "$temporary_directory/bootstrap-task-definition.json" \
  bootstrap)"

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
    --task-definition "$bootstrap_task_definition" \
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

if [[ "$rollback" == false ]]; then
  run_bootstrap_task alembic upgrade head
  if [[ "$initialize_ledger" == true ]]; then
    run_bootstrap_task python -m app.deletion_ledger initialize
  fi
fi

aws ecs update-service \
  --region "$region" \
  --cluster "$cluster" \
  --service "$service" \
  --task-definition "$app_task_definition" \
  --desired-count 1 >/dev/null
aws ecs wait services-stable --region "$region" --cluster "$cluster" --services "$service"

service_state="$(aws ecs describe-services \
  --region "$region" \
  --cluster "$cluster" \
  --services "$service" \
  --query 'services[0].[taskDefinition,runningCount,desiredCount]' \
  --output text)"
read -r deployed_task_definition running_count desired_count <<<"$service_state"
if [[ "$deployed_task_definition" != "$app_task_definition" ||
  "$running_count" != "1" ||
  "$desired_count" != "1" ]]; then
  printf 'The ECS service did not stabilize on the requested image task definition.\n' >&2
  exit 1
fi

uat_url="$(deployment_output uat_url)"
printf 'Owner-beta task definition now references image %s.\n' "$image_tag"
printf 'Application task definition: %s\n' "$app_task_definition"
printf 'Bootstrap task definition: %s\n' "$bootstrap_task_definition"
printf 'Owner-beta UAT endpoint: %s\n' "$uat_url"
if [[ "$rollback" == true ]]; then
  printf 'The rollback changed application tasks only; it did not reverse database migrations.\n' >&2
fi
