#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
command -v aws >/dev/null
command -v terraform >/dev/null
command -v python3 >/dev/null

if [[ "$#" -ne 0 ]]; then
  printf 'Usage: %s\n' "$0" >&2
  exit 2
fi

confirmation_phrase="RESET OWNER-BETA UAT CASE"
printf 'This permanently deletes the registered UAT case and all of its stored object versions.\n'
printf 'The owner account and permanent-deletion ledger are preserved.\n'
read -r -p "Type \"$confirmation_phrase\" to continue: " confirmation
if [[ "$confirmation" != "$confirmation_phrase" ]]; then
  printf 'Confirmation did not match; no UAT data was changed.\n' >&2
  exit 2
fi

region="${AWS_REGION:-$(terraform -chdir="$script_dir" output -raw aws_region)}"
account_id="$(terraform -chdir="$script_dir" output -raw aws_account_id)"
cluster="$(terraform -chdir="$script_dir" output -raw ecs_cluster_name)"
bootstrap_task="$(terraform -chdir="$script_dir" output -raw bootstrap_task_definition_arn)"
subnets="$(terraform -chdir="$script_dir" output -raw public_subnet_ids)"
security_group="$(terraform -chdir="$script_dir" output -raw app_security_group_id)"
caller_account="$(aws sts get-caller-identity --query Account --output text)"

if [[ "$caller_account" != "$account_id" ]]; then
  printf 'AWS caller account does not match the Terraform deployment account.\n' >&2
  exit 1
fi

overrides="$(python3 - "$confirmation_phrase" <<'PY'
import json
import sys

print(json.dumps({
    "containerOverrides": [{
        "name": "bootstrap",
        "command": [
            "python",
            "-m",
            "app.uat_fixtures",
            "--confirmation",
            sys.argv[1],
        ],
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
  printf 'Could not start the UAT reset task.\n' >&2
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
  printf 'UAT reset task failed; inspect its redacted CloudWatch logs.\n' >&2
  exit 1
fi

printf 'Owner-beta UAT case reset completed. The account is ready to start a new synthetic case.\n'
