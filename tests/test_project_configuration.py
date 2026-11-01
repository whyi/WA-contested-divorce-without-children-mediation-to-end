import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ProjectConfigurationTests(unittest.TestCase):
    def test_project_declares_specified_stack(self) -> None:
        with (ROOT / "pyproject.toml").open("rb") as project_file:
            project = tomllib.load(project_file)["project"]

        self.assertEqual(project["requires-python"], ">=3.11")
        dependencies = set(project["dependencies"])
        for package in (
            "fastapi",
            "sqlalchemy",
            "psycopg",
            "boto3",
            "docxtpl",
            "docx2pdf",
            "pdf2docx",
            "python-docx",
            "pymupdf",
            "pypdf",
            "pwdlib",
            "pyotp",
            "pyjwt",
            "webauthn",
            "email-validator",
        ):
            self.assertTrue(
                any(dependency.lower().startswith(package.lower()) for dependency in dependencies),
                f"Missing required stack dependency: {package}",
            )

    def test_docker_build_installs_libreoffice(self) -> None:
        dockerfile = (ROOT / "Dockerfile").read_text()
        self.assertIn("libreoffice-writer", dockerfile)

    def test_compose_provides_postgres_and_moto_s3(self) -> None:
        compose = (ROOT / "docker-compose.yml").read_text()
        self.assertIn("image: postgres:", compose)
        self.assertIn("image: motoserver/moto:", compose)
        self.assertIn("extraction-worker:", compose)
        self.assertIn('"app.extraction_worker"', compose)
        self.assertIn("analysis-worker:", compose)
        self.assertIn('"app.analysis_worker"', compose)
        analysis_worker = (ROOT / "src" / "app" / "analysis_worker.py").read_text()
        self.assertIn('if __name__ == "__main__":\n    main()', analysis_worker)

    def test_compose_demo_login_is_explicit_and_case_data_remains_disabled(self) -> None:
        compose = (ROOT / "docker-compose.yml").read_text()

        self.assertIn('DEMO_MODE_ENABLED: "${DEMO_MODE_ENABLED:-true}"', compose)
        self.assertIn('AUTH_ENABLED: "${AUTH_ENABLED:-true}"', compose)
        self.assertIn('CASE_DATA_ENABLED: "${CASE_DATA_ENABLED:-false}"', compose)
        self.assertIn('CASE_MATERIALS_ENABLED: "${CASE_MATERIALS_ENABLED:-false}"', compose)
        self.assertIn('AI_ANALYSIS_ENABLED: "${AI_ANALYSIS_ENABLED:-false}"', compose)
        self.assertIn('AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID:-test}', compose)
        self.assertIn('BEDROCK_MODEL_ID: ${BEDROCK_MODEL_ID:-}', compose)
        analysis_worker = compose.split("  analysis-worker:", 1)[1]
        self.assertIn('S3_KMS_KEY_ID: ${S3_KMS_KEY_ID:-}', analysis_worker)
        self.assertIn("local-demo-only-signing-secret-not-for-production", compose)

    def test_package_includes_the_landing_page_asset(self) -> None:
        with (ROOT / "pyproject.toml").open("rb") as project_file:
            project = tomllib.load(project_file)

        self.assertEqual(
            project["tool"]["setuptools"]["package-data"]["app"],
            ["static/*.html"],
        )
