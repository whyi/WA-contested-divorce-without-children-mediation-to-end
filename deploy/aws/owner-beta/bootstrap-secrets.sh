#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
command -v aws >/dev/null
command -v terraform >/dev/null
command -v python3 >/dev/null
command -v openssl >/dev/null

region="${AWS_REGION:-$(terraform -chdir="$script_dir" output -raw aws_region)}"
master_secret_arn="$(terraform -chdir="$script_dir" output -raw rds_master_secret_arn)"
database_name="$(terraform -chdir="$script_dir" output -raw uat_database_name)"
database_instance_id="$(terraform -chdir="$script_dir" output -raw ecs_cluster_name)"
secret_names="$(terraform -chdir="$script_dir" output -json application_secret_names)"
temporary_directory="$(mktemp -d)"
chmod 700 "$temporary_directory"
trap 'rm -rf -- "$temporary_directory"' EXIT

aws secretsmanager get-secret-value \
  --region "$region" \
  --secret-id "$master_secret_arn" \
  --query SecretString \
  --output text >"$temporary_directory/rds-secret.json"

aws rds describe-db-instances \
  --region "$region" \
  --db-instance-identifier "$database_instance_id" \
  --query 'DBInstances[0].Endpoint' \
  --output json >"$temporary_directory/rds-endpoint.json"

python3 "$script_dir/database_url.py" \
  "$temporary_directory/rds-secret.json" \
  "$temporary_directory/rds-endpoint.json" \
  "$database_name" \
  "$temporary_directory/database-url"

put_secret() {
  local secret_name="$1"
  local value="$2"
  local secret_file="$temporary_directory/secret-value"
  printf '%s' "$value" >"$secret_file"
  aws secretsmanager put-secret-value \
    --region "$region" \
    --secret-id "$secret_name" \
    --secret-string "file://$secret_file" >/dev/null
  rm -f -- "$secret_file"
}

secret_name() {
  python3 -c 'import json,sys; print(json.load(sys.stdin)[sys.argv[1]])' \
    "$1" <<<"$secret_names"
}

secret_is_populated() {
  local secret_id="$1"
  local current_version
  current_version="$(aws secretsmanager describe-secret \
    --region "$region" \
    --secret-id "$secret_id" \
    --query 'VersionIdsToStages.*[]' \
    --output text)"
  [[ -n "$current_version" && "$current_version" != "None" ]]
}

database_url_name="$(secret_name database_url)"
auth_jwt_name="$(secret_name auth_jwt)"
auth_encryption_name="$(secret_name auth_encryption)"
owner_email_name="$(secret_name owner_email)"
auth_email_from_name="$(secret_name auth_email_from)"
smtp_username_name="$(secret_name smtp_username)"
smtp_password_name="$(secret_name smtp_password)"
database_url_populated=false
auth_jwt_populated=false
auth_encryption_populated=false
owner_email_populated=false
auth_email_from_populated=false
smtp_username_populated=false
smtp_password_populated=false
secret_is_populated "$database_url_name" && database_url_populated=true
secret_is_populated "$auth_jwt_name" && auth_jwt_populated=true
secret_is_populated "$auth_encryption_name" && auth_encryption_populated=true
secret_is_populated "$owner_email_name" && owner_email_populated=true
secret_is_populated "$auth_email_from_name" && auth_email_from_populated=true
secret_is_populated "$smtp_username_name" && smtp_username_populated=true
secret_is_populated "$smtp_password_name" && smtp_password_populated=true

if [[ "$database_url_populated" == true &&
  "$auth_jwt_populated" == true &&
  "$auth_encryption_populated" == true &&
  "$owner_email_populated" == true &&
  "$auth_email_from_populated" == true &&
  "$smtp_username_populated" == true &&
  "$smtp_password_populated" == true ]]; then
  printf 'Runtime secrets are already populated; no values were changed.\n'
  exit 0
fi

if [[ "$owner_email_populated" == false ]]; then
  read -r -p "Verified owner email (must also be verified in SES sandbox): " owner_email
fi
if [[ "$auth_email_from_populated" == false ]]; then
  read -r -p "SES sender email, verified in SES (blank = owner email; use a different address if the mailbox provider drops mail from itself): " auth_email_from
  auth_email_from="${auth_email_from:-${owner_email:-}}"
  if [[ -z "$auth_email_from" ]]; then
    auth_email_from="$(aws secretsmanager get-secret-value \
      --region "$region" \
      --secret-id "$owner_email_name" \
      --query SecretString \
      --output text)"
  fi
fi
if [[ "$smtp_username_populated" == false ]]; then
  read -r -p "SES SMTP username: " smtp_username
fi
if [[ "$smtp_password_populated" == false ]]; then
  read -r -s -p "SES SMTP password: " smtp_password
  printf '\n'
fi

if [[ "$database_url_populated" == false ]]; then
  aws secretsmanager put-secret-value \
    --region "$region" \
    --secret-id "$database_url_name" \
    --secret-string "file://$temporary_directory/database-url" >/dev/null
fi
if [[ "$auth_jwt_populated" == false ]]; then
  put_secret "$auth_jwt_name" "$(openssl rand -hex 32)"
fi
if [[ "$auth_encryption_populated" == false ]]; then
  put_secret "$auth_encryption_name" "$(openssl rand -hex 32)"
fi
if [[ "$owner_email_populated" == false ]]; then
  put_secret "$owner_email_name" "$owner_email"
fi
if [[ "$auth_email_from_populated" == false ]]; then
  put_secret "$auth_email_from_name" "$auth_email_from"
fi
if [[ "$smtp_username_populated" == false ]]; then
  put_secret "$smtp_username_name" "$smtp_username"
fi
if [[ "$smtp_password_populated" == false ]]; then
  put_secret "$smtp_password_name" "$smtp_password"
fi

unset owner_email auth_email_from smtp_username smtp_password 2>/dev/null || true
printf 'UAT runtime secrets were stored in AWS Secrets Manager; secret values were not printed.\n'
