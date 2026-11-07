from copy import deepcopy
import json
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
) -> dict[str, Any]:
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
    )
    with Path(output_path).open("w", encoding="utf-8") as output_file:
        json.dump(task_definition, output_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
