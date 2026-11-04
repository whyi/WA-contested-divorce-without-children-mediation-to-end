import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock, patch


MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "versions"
    / "0012_sent_confirmation_freeze.py"
)
MIGRATION_SPEC = importlib.util.spec_from_file_location(
    "sent_confirmation_freeze_migration",
    MIGRATION_PATH,
)
if MIGRATION_SPEC is None or MIGRATION_SPEC.loader is None:
    raise RuntimeError(f"Unable to load migration at {MIGRATION_PATH}")

migration = importlib.util.module_from_spec(MIGRATION_SPEC)
MIGRATION_SPEC.loader.exec_module(migration)


class SentConfirmationFreezeMigrationTests(unittest.TestCase):
    def test_revision_and_parent_are_valid(self) -> None:
        self.assertLessEqual(len(migration.revision), 32)
        self.assertEqual(migration.down_revision, "0011_settlement_attempts")

    def test_upgrade_adds_confirmation_timestamp_and_preserves_legacy_frozen_rows(self) -> None:
        operations = Mock()
        with patch.object(migration, "op", operations):
            migration.upgrade()

        operations.add_column.assert_called_once()
        self.assertEqual(operations.add_column.call_args.args[0], "settlement_negotiation_attempts")
        operations.execute.assert_called_once()
        sql = str(operations.execute.call_args.args[0])
        self.assertIn("sent_confirmed_at = frozen_at", sql)
        self.assertIn("WHERE frozen_at IS NOT NULL", sql)

    def test_downgrade_removes_confirmation_timestamp(self) -> None:
        operations = Mock()
        with patch.object(migration, "op", operations):
            migration.downgrade()
        operations.drop_column.assert_called_once_with(
            "settlement_negotiation_attempts",
            "sent_confirmed_at",
        )


if __name__ == "__main__":
    unittest.main()
