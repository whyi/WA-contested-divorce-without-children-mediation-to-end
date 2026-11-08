import importlib.util
import json
import os
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch


DEPLOYMENT_DIR = Path(__file__).parents[1] / "deploy/aws/owner-beta"
SPEC = importlib.util.spec_from_file_location(
    "owner_beta_deployment_config", DEPLOYMENT_DIR / "deployment_config.py"
)
if SPEC is None or SPEC.loader is None:
    raise ImportError("Could not load deployment configuration helper.")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class DeploymentConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = {
            "aws_account_id": "123456789012",
            "aws_region": "us-west-2",
            "ecr_repository_url": "123456789012.dkr.ecr.us-west-2.amazonaws.com/owner-beta",
            "ecs_cluster_name": "owner-beta",
            "ecs_service_name": "owner-beta",
            "app_task_definition_arn": "arn:aws:ecs:us-west-2:123456789012:task-definition/owner-beta:1",
            "bootstrap_task_definition_arn": "arn:aws:ecs:us-west-2:123456789012:task-definition/owner-beta-bootstrap:1",
            "public_subnet_ids": "subnet-abc123,subnet-def456",
            "app_security_group_id": "sg-abc123",
            "uat_url": "https://example.execute-api.us-west-2.amazonaws.com",
        }

    def test_validates_complete_configuration(self) -> None:
        self.assertEqual(MODULE.validate_config(self.config), self.config)

    def test_rejects_missing_or_invalid_settings(self) -> None:
        for name in self.config:
            for invalid in (None, "", "invalid\ninjected-value"):
                with self.subTest(name=name, invalid=invalid):
                    with self.assertRaisesRegex(ValueError, name):
                        MODULE.validate_config({**self.config, name: invalid})

    def test_rejects_cross_account_targets(self) -> None:
        for name in (
            "ecr_repository_url",
            "app_task_definition_arn",
            "bootstrap_task_definition_arn",
        ):
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, "deployment account"):
                    MODULE.validate_config(
                        {**self.config, name: self.config[name].replace("123456789012", "987654321098")}
                    )

    def test_export_selects_only_deployment_settings(self) -> None:
        outputs = {name: {"value": value} for name, value in self.config.items()}
        outputs["other_sensitive_output"] = {"value": "do-not-export"}
        result = subprocess.run(
            ["python3", str(DEPLOYMENT_DIR / "deployment_config.py"), "export"],
            input=json.dumps(outputs),
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(json.loads(result.stdout), self.config)

    def test_shell_helper_reads_configuration_without_terraform(self) -> None:
        result = subprocess.run(
            [
                "bash", "-e", "-c",
                'script_dir="$1"; source "$script_dir/deployment-output.sh"; deployment_output uat_url',
                "test", str(DEPLOYMENT_DIR),
            ],
            env={**os.environ, "UAT_DEPLOYMENT_OUTPUTS_JSON": json.dumps(self.config)},
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(result.stdout.strip(), self.config["uat_url"])

    def test_shell_helper_preserves_local_terraform_output(self) -> None:
        result = subprocess.run(
            [
                "bash", "-e", "-c",
                'script_dir="$1"; source "$script_dir/deployment-output.sh"; '
                'terraform() { printf "%s\\n" "$*"; }; deployment_output aws_account_id',
                "test", str(DEPLOYMENT_DIR),
            ],
            env={**os.environ, "UAT_DEPLOYMENT_OUTPUTS_JSON": ""},
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(result.stdout.strip(), f"-chdir={DEPLOYMENT_DIR} output -raw aws_account_id")

    def test_bad_configuration_does_not_print_values(self) -> None:
        with patch.dict(os.environ, {"UAT_DEPLOYMENT_OUTPUTS_JSON": '{"aws_account_id":"secret-value"}'}):
            result = subprocess.run(
                ["python3", str(DEPLOYMENT_DIR / "deployment_config.py"), "validate"],
                text=True,
                capture_output=True,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("secret-value", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
