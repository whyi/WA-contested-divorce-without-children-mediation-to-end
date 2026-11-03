import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock, patch


MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "versions"
    / "0008_settlement_planning.py"
)
MIGRATION_SPEC = importlib.util.spec_from_file_location(
    "settlement_planning_migration",
    MIGRATION_PATH,
)
if MIGRATION_SPEC is None or MIGRATION_SPEC.loader is None:
    raise RuntimeError(f"Unable to load migration at {MIGRATION_PATH}")

migration = importlib.util.module_from_spec(MIGRATION_SPEC)
MIGRATION_SPEC.loader.exec_module(migration)


class SettlementPlanningMigrationTests(unittest.TestCase):
    def test_revision_fits_alembic_version_column(self) -> None:
        self.assertLessEqual(len(migration.revision), 32)
        self.assertEqual(migration.down_revision, "0007_property_tracing")

    def test_upgrade_adds_revision_and_append_only_tables(self) -> None:
        operations = Mock()
        with patch.object(migration, "op", operations):
            migration.upgrade()

        self.assertEqual(
            [call.args[0] for call in operations.create_table.call_args_list],
            [
                "settlement_planning_consent_events",
                "settlement_ledger_events",
                "settlement_scenario_runs",
                "settlement_scenario_selections",
            ],
        )
        self.assertEqual(operations.add_column.call_count, 7)
        self.assertEqual(operations.create_index.call_count, 5)

    def test_downgrade_removes_tables_before_case_revision(self) -> None:
        operations = Mock()
        with patch.object(migration, "op", operations):
            migration.downgrade()

        self.assertEqual(
            [call.args[0] for call in operations.drop_table.call_args_list],
            [
                "settlement_scenario_selections",
                "settlement_scenario_runs",
                "settlement_ledger_events",
                "settlement_planning_consent_events",
            ],
        )
        operations.drop_column.assert_called_once_with("cases", "settlement_revision")


if __name__ == "__main__":
    unittest.main()
