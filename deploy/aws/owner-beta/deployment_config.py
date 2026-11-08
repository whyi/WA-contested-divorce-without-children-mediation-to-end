import json
import os
import re
import sys
from typing import Any


def validate_config(config: dict[str, Any]) -> dict[str, str]:
    patterns = {
        "aws_account_id": r"\d{12}",
        "aws_region": r"us-west-2",
        "ecr_repository_url": r"\d{12}\.dkr\.ecr\.us-west-2\.amazonaws\.com/[a-z0-9][a-z0-9/_-]*",
        "ecs_cluster_name": r"[a-zA-Z0-9_-]+",
        "ecs_service_name": r"[a-zA-Z0-9_-]+",
        "app_task_definition_arn": r"arn:aws:ecs:us-west-2:\d{12}:task-definition/[a-zA-Z0-9_-]+:\d+",
        "bootstrap_task_definition_arn": r"arn:aws:ecs:us-west-2:\d{12}:task-definition/[a-zA-Z0-9_-]+:\d+",
        "public_subnet_ids": r"subnet-[0-9a-f]+(?:,subnet-[0-9a-f]+)*",
        "app_security_group_id": r"sg-[0-9a-f]+",
        "uat_url": r"https://[a-z0-9]+\.execute-api\.us-west-2\.amazonaws\.com/?",
    }
    result = {}
    for name, pattern in patterns.items():
        value = config.get(name)
        if not isinstance(value, str) or re.fullmatch(pattern, value) is None:
            raise ValueError(f"Missing or invalid deployment setting: {name}")
        result[name] = value
    account = result["aws_account_id"]
    if not result["ecr_repository_url"].startswith(f"{account}."):
        raise ValueError("ECR repository does not match the deployment account.")
    for name in ("app_task_definition_arn", "bootstrap_task_definition_arn"):
        if result[name].split(":")[4] != account:
            raise ValueError(f"{name} does not match the deployment account.")
    return result


def main() -> None:
    if sys.argv[1:] == ["export"]:
        outputs = json.load(sys.stdin)
        config = validate_config({key: value["value"] for key, value in outputs.items()})
        print(json.dumps(config))
        return
    if len(sys.argv) != 2:
        raise ValueError("Usage: deployment_config.py export | SETTING_NAME")
    config = validate_config(json.loads(os.environ["UAT_DEPLOYMENT_OUTPUTS_JSON"]))
    if sys.argv[1] == "validate":
        return
    print(config[sys.argv[1]])


if __name__ == "__main__":
    main()
