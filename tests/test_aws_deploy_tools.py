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

DATABASE_URL_PATH = (
    Path(__file__).parents[1]
    / "deploy"
    / "aws"
    / "owner-beta"
    / "database_url.py"
)
DATABASE_URL_SPEC = importlib.util.spec_from_file_location(
    "owner_beta_database_url",
    DATABASE_URL_PATH,
)
if DATABASE_URL_SPEC is None or DATABASE_URL_SPEC.loader is None:
    raise ImportError(f"Could not load {DATABASE_URL_PATH}")
DATABASE_URL_MODULE = importlib.util.module_from_spec(DATABASE_URL_SPEC)
DATABASE_URL_SPEC.loader.exec_module(DATABASE_URL_MODULE)
build_database_url = DATABASE_URL_MODULE.build_database_url


class TaskDefinitionImageTests(unittest.TestCase):
    def test_injects_google_configuration_without_reading_secret_or_losing_settings(self) -> None:
        secret_arn = "arn:aws:secretsmanager:us-west-2:123456789012:secret:google-secret-abcdef"
        described = {
            "executionRoleArn": "arn:aws:iam::123456789012:role/execution",
            "containerDefinitions": [{
                "name": "api",
                "environment": [
                    {"name": "OWNER_BETA_ENABLED", "value": "true"},
                    {"name": "GOOGLE_CLIENT_SECRET", "value": "old-plaintext"},
                    {"name": "GOOGLE_CLIENT_ID", "value": "old-client"},
                ],
                "secrets": [{"name": "DATABASE_URL", "valueFrom": "database-arn"}],
            }, {"name": "worker"}],
        }
        result = task_definition_for_image(
            described, "repo:latest", "api",
            google_client_id="synthetic.apps.googleusercontent.com",
            google_client_secret_arn=secret_arn,
        )
        for container in result["containerDefinitions"]:
            self.assertIn(
                {"name": "GOOGLE_CLIENT_ID", "value": "synthetic.apps.googleusercontent.com"},
                container["environment"],
            )
            self.assertIn(
                {"name": "GOOGLE_CLIENT_SECRET", "valueFrom": secret_arn},
                container["secrets"],
            )
            self.assertFalse(any(entry["name"] == "GOOGLE_CLIENT_SECRET" for entry in container["environment"]))
        self.assertIn({"name": "OWNER_BETA_ENABLED", "value": "true"}, result["containerDefinitions"][0]["environment"])
        self.assertEqual(len(described["containerDefinitions"][0]["environment"]), 3)

    def test_rejects_partial_or_wrong_account_google_configuration(self) -> None:
        described = {
            "executionRoleArn": "arn:aws:iam::123456789012:role/execution",
            "containerDefinitions": [{"name": "api"}],
        }
        for client, secret in [
            ("synthetic.apps.googleusercontent.com", ""),
            ("", "arn:aws:secretsmanager:us-west-2:123456789012:secret:google-secret"),
            ("invalid", "arn:aws:secretsmanager:us-west-2:123456789012:secret:google-secret"),
            ("synthetic.apps.googleusercontent.com", "plaintext-not-an-arn"),
            ("synthetic.apps.googleusercontent.com", "arn:aws:secretsmanager:us-west-2:999999999999:secret:google-secret"),
        ]:
            with self.subTest(client=client, secret=secret), self.assertRaises(ValueError):
                task_definition_for_image(
                    described, "repo:latest", "api",
                    google_client_id=client, google_client_secret_arn=secret,
                )

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


class DatabaseUrlTests(unittest.TestCase):
    def test_builds_tls_url_from_rds_secret_and_endpoint(self) -> None:
        url = build_database_url(
            {"username": "case@work", "password": "p:a/ss"},
            {"Address": "db.example.internal", "Port": 5432},
            "owner_beta_uat",
        )

        self.assertEqual(
            url,
            "postgresql+psycopg://case%40work:p%3Aa%2Fss"
            "@db.example.internal:5432/owner_beta_uat?sslmode=require",
        )

    def test_reports_missing_rds_endpoint_without_reading_secret_values(self) -> None:
        with self.assertRaisesRegex(ValueError, "endpoint is not available"):
            build_database_url(
                {"username": "casework", "password": "not-printed"},
                {},
                "owner_beta_uat",
            )


if __name__ == "__main__":
    unittest.main()
