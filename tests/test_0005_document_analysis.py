import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock, patch


MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "versions"
    / "0005_document_analysis.py"
)
MIGRATION_SPEC = importlib.util.spec_from_file_location(
    "document_analysis_migration",
    MIGRATION_PATH,
)
if MIGRATION_SPEC is None or MIGRATION_SPEC.loader is None:
    raise RuntimeError(f"Unable to load migration at {MIGRATION_PATH}")

migration = importlib.util.module_from_spec(MIGRATION_SPEC)
MIGRATION_SPEC.loader.exec_module(migration)


class DocumentAnalysisMigrationTests(unittest.TestCase):
    def test_upgrade_creates_consent_request_job_and_proposal_tables(self) -> None:
        operations = Mock()
        with patch.object(migration, "op", operations):
            migration.upgrade()

        tables = [call.args[0] for call in operations.create_table.call_args_list]
        self.assertEqual(
            tables,
            [
                "document_analysis_consents",
                "document_analysis_requests",
                "document_analysis_jobs",
                "document_analysis_proposals",
            ],
        )
        self.assertGreaterEqual(operations.create_index.call_count, 1)

    def test_downgrade_removes_analysis_tables_in_dependency_order(self) -> None:
        operations = Mock()
        with patch.object(migration, "op", operations):
            migration.downgrade()

        self.assertEqual(
            [call.args[0] for call in operations.drop_table.call_args_list],
            [
                "document_analysis_proposals",
                "document_analysis_jobs",
                "document_analysis_requests",
                "document_analysis_consents",
            ],
        )


if __name__ == "__main__":
    unittest.main()
