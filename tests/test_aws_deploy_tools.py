import importlib.util
import unittest
from pathlib import Path

TASK_DEFINITION_PATH = (
    Path(__file__).parents[1]
    / "deploy"
    / "aws"
    / "owner-beta"
    / "task_definition.py"
)
TASK_DEFINITION_SPEC = importlib.util.spec_from_file_location(
    "owner_beta_task_definition",
    TASK_DEFINITION_PATH,
)
if TASK_DEFINITION_SPEC is None or TASK_DEFINITION_SPEC.loader is None:
    raise ImportError(f"Could not load {TASK_DEFINITION_PATH}")
TASK_DEFINITION_MODULE = importlib.util.module_from_spec(TASK_DEFINITION_SPEC)
TASK_DEFINITION_SPEC.loader.exec_module(TASK_DEFINITION_MODULE)
task_definition_for_image = TASK_DEFINITION_MODULE.task_definition_for_image


class TaskDefinitionImageTests(unittest.TestCase):
    def test_replaces_all_container_images_and_strips_describe_only_fields(self) -> None:
        described = {
            "family": "owner-beta",
            "taskDefinitionArn": "arn:aws:ecs:us-west-2:123456789012:task-definition/owner-beta:4",
            "revision": 4,
            "status": "ACTIVE",
            "requiresCompatibilities": ["FARGATE"],
            "containerDefinitions": [
                {"name": "api", "image": "repo:bootstrap"},
                {"name": "extraction-worker", "image": "repo:bootstrap"},
            ],
        }

        result = task_definition_for_image(
            described,
            "repo:commit-123",
            "api",
        )

        self.assertEqual(
            [container["image"] for container in result["containerDefinitions"]],
            ["repo:commit-123", "repo:commit-123"],
        )
        self.assertNotIn("taskDefinitionArn", result)
        self.assertNotIn("revision", result)
        self.assertNotIn("status", result)
        self.assertEqual(
            [container["image"] for container in described["containerDefinitions"]],
            ["repo:bootstrap", "repo:bootstrap"],
        )

    def test_rejects_task_definition_without_expected_container(self) -> None:
        with self.assertRaisesRegex(ValueError, "expected container 'bootstrap'"):
            task_definition_for_image(
                {
                    "family": "owner-beta-bootstrap",
                    "containerDefinitions": [{"name": "api", "image": "repo:bootstrap"}],
                },
                "repo:commit-123",
                "bootstrap",
            )


if __name__ == "__main__":
    unittest.main()
