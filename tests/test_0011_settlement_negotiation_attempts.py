import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock, patch


MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "versions"
    / "0011_settlement_negotiation_attempts.py"
)
MIGRATION_SPEC = importlib.util.spec_from_file_location(
    "settlement_negotiation_attempts_migration",
    MIGRATION_PATH,
)
if MIGRATION_SPEC is None or MIGRATION_SPEC.loader is None:
    raise RuntimeError(f"Unable to load migration at {MIGRATION_PATH}")

migration = importlib.util.module_from_spec(MIGRATION_SPEC)
MIGRATION_SPEC.loader.exec_module(migration)


class SettlementNegotiationAttemptMigrationTests(unittest.TestCase):
    def test_revision_fits_alembic_version_column(self) -> None:
        self.assertLessEqual(len(migration.revision), 32)
        self.assertEqual(migration.down_revision, "0010_settlement_offer_response")

    def test_upgrade_creates_ordinal_and_predecessor_constraints(self) -> None:
        operations = Mock()
        with patch.object(migration, "op", operations):
            migration.upgrade()

        self.assertEqual(operations.create_table.call_args.args[0], "settlement_negotiation_attempts")
        constraints = operations.create_table.call_args.args[1:]
        self.assertTrue(
            any(getattr(item, "name", "") == "uq_settlement_negotiation_attempt_case_ordinal"
                for item in constraints)
        )
        self.assertTrue(
            any(getattr(item, "name", "") == "uq_settlement_negotiation_attempt_predecessor"
                for item in constraints)
        )
        self.assertEqual(operations.create_index.call_count, 3)

    def test_downgrade_removes_attempt_table(self) -> None:
        operations = Mock()
        with patch.object(migration, "op", operations):
            migration.downgrade()
        operations.drop_table.assert_called_once_with("settlement_negotiation_attempts")


if __name__ == "__main__":
    unittest.main()
