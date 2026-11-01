import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock, patch


MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "versions"
    / "0006_proposal_review_and_adoption.py"
)
MIGRATION_SPEC = importlib.util.spec_from_file_location(
    "proposal_review_and_adoption_migration",
    MIGRATION_PATH,
)
if MIGRATION_SPEC is None or MIGRATION_SPEC.loader is None:
    raise RuntimeError(f"Unable to load migration at {MIGRATION_PATH}")

migration = importlib.util.module_from_spec(MIGRATION_SPEC)
MIGRATION_SPEC.loader.exec_module(migration)


class ProposalReviewMigrationTests(unittest.TestCase):
    def test_revision_fits_alembic_version_column(self) -> None:
        self.assertLessEqual(len(migration.revision), 32)

    def test_upgrade_adds_profile_revision_and_review_adoption_tables(self) -> None:
        operations = Mock()
        with patch.object(migration, "op", operations):
            migration.upgrade()

        self.assertEqual(
            [call.args[0] for call in operations.create_table.call_args_list],
            [
                "analysis_proposal_review_events",
                "case_profile_adoptions",
                "case_profile_facts",
                "case_profile_fact_events",
            ],
        )
        operations.add_column.assert_called_once()
        self.assertGreaterEqual(operations.create_index.call_count, 1)

    def test_downgrade_removes_tables_before_profile_revision(self) -> None:
        operations = Mock()
        with patch.object(migration, "op", operations):
            migration.downgrade()

        self.assertEqual(
            [call.args[0] for call in operations.drop_table.call_args_list],
            [
                "case_profile_fact_events",
                "case_profile_facts",
                "case_profile_adoptions",
                "analysis_proposal_review_events",
            ],
        )
        operations.drop_column.assert_called_once_with("cases", "profile_revision")


if __name__ == "__main__":
    unittest.main()
