import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock, patch


MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "versions"
    / "0004_document_extraction_jobs.py"
)
MIGRATION_SPEC = importlib.util.spec_from_file_location(
    "document_extraction_jobs_migration",
    MIGRATION_PATH,
)
if MIGRATION_SPEC is None or MIGRATION_SPEC.loader is None:
    raise RuntimeError(f"Unable to load migration at {MIGRATION_PATH}")

migration = importlib.util.module_from_spec(MIGRATION_SPEC)
MIGRATION_SPEC.loader.exec_module(migration)


class DocumentExtractionJobMigrationTests(unittest.TestCase):
    def test_upgrade_adds_page_provenance_and_durable_jobs(self) -> None:
        operations = Mock()
        with patch.object(migration, "op", operations):
            migration.upgrade()

        self.assertEqual(
            [call.args[0] for call in operations.create_table.call_args_list],
            ["document_extraction_jobs"],
        )
        self.assertEqual(
            operations.add_column.call_args.args[1].name,
            "pages_json",
        )
        job_columns = {
            column.name
            for column in operations.create_table.call_args.args[1:]
            if hasattr(column, "name")
        }
        self.assertTrue(
            {
                "document_id",
                "source_sha256",
                "request_id",
                "status",
                "attempts",
                "lease_token",
                "lease_expires_at",
                "error_code",
            }.issubset(job_columns)
        )
        self.assertGreaterEqual(operations.create_index.call_count, 1)

    def test_downgrade_removes_jobs_and_page_provenance(self) -> None:
        operations = Mock()
        with patch.object(migration, "op", operations):
            migration.downgrade()

        operations.drop_table.assert_called_once_with("document_extraction_jobs")
        operations.drop_column.assert_called_once_with(
            "document_extractions",
            "pages_json",
        )


if __name__ == "__main__":
    unittest.main()
