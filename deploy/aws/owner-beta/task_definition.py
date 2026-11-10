from copy import deepcopy
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

REGISTERABLE_FIELDS = {
    "family",
    "taskRoleArn",
    "executionRoleArn",
    "networkMode",
    "containerDefinitions",
    "volumes",
    "placementConstraints",
    "requiresCompatibilities",
    "cpu",
    "memory",
    "tags",
    "pidMode",
    "ipcMode",
    "proxyConfiguration",
    "inferenceAccelerators",
    "ephemeralStorage",
    "runtimePlatform",
    "enableFaultInjection",
}


def task_definition_for_image(
    described_task_definition: dict[str, Any],
    image: str,
    required_container_name: str,
    *,
    google_client_id: str = "",
    google_client_secret_arn: str = "",
) -> dict[str, Any]:
    if bool(google_client_id) != bool(google_client_secret_arn):
        raise ValueError("Google client ID and secret ARN must be configured together.")
    if google_client_id:
        if not re.fullmatch(r"[a-zA-Z0-9._-]+\.apps\.googleusercontent\.com", google_client_id):
            raise ValueError("Invalid Google OAuth client ID.")
        if not re.fullmatch(
            r"arn:aws:secretsmanager:us-west-2:\d{12}:secret:[a-zA-Z0-9/_+=.@-]+",
            google_client_secret_arn,
        ):
            raise ValueError("Google secret must be a Secrets Manager ARN in us-west-2.")
        execution_role = described_task_definition.get("executionRoleArn", "")
        if execution_role.split(":")[4:5] != google_client_secret_arn.split(":")[4:5]:
            raise ValueError("Google secret must belong to the task execution role's AWS account.")
    task_definition = {
        key: deepcopy(value)
        for key, value in described_task_definition.items()
        if key in REGISTERABLE_FIELDS
    }
    containers = task_definition.get("containerDefinitions", [])
    if not containers or not any(
        container.get("name") == required_container_name for container in containers
    ):
        raise ValueError(
            f"Base task definition does not contain expected container "
            f"{required_container_name!r}."
        )
    for container in containers:
        container["image"] = image
        if google_client_id:
            names = {"GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"}
            container["environment"] = [
                entry for entry in container.get("environment", []) if entry["name"] not in names
            ] + [{"name": "GOOGLE_CLIENT_ID", "value": google_client_id}]
            container["secrets"] = [
                entry for entry in container.get("secrets", []) if entry["name"] not in names
            ] + [{"name": "GOOGLE_CLIENT_SECRET", "valueFrom": google_client_secret_arn}]
    return task_definition


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 4:
        print(
            "Usage: task_definition.py SOURCE_JSON OUTPUT_JSON IMAGE CONTAINER_NAME",
            file=sys.stderr,
        )
        return 2
    source_path, output_path, image, required_container_name = args
    with Path(source_path).open(encoding="utf-8") as source_file:
        described = json.load(source_file)
    task_definition = task_definition_for_image(
        described,
        image,
        required_container_name,
        google_client_id=os.environ.get("UAT_GOOGLE_CLIENT_ID", ""),
        google_client_secret_arn=os.environ.get("UAT_GOOGLE_CLIENT_SECRET_ARN", ""),
    )
    with Path(output_path).open("w", encoding="utf-8") as output_file:
        json.dump(task_definition, output_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
