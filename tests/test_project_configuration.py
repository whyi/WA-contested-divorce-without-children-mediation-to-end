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

    def test_package_includes_the_landing_page_asset(self) -> None:
        with (ROOT / "pyproject.toml").open("rb") as project_file:
            project = tomllib.load(project_file)

        self.assertEqual(
            project["tool"]["setuptools"]["package-data"]["app"],
            ["static/*.html"],
        )
