import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock, patch


MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "versions"
    / "0009_cr2a_property_exports.py"
)
MIGRATION_SPEC = importlib.util.spec_from_file_location(
    "cr2a_property_exports_migration",
    MIGRATION_PATH,
)
if MIGRATION_SPEC is None or MIGRATION_SPEC.loader is None:
    raise RuntimeError(f"Unable to load migration at {MIGRATION_PATH}")

migration = importlib.util.module_from_spec(MIGRATION_SPEC)
MIGRATION_SPEC.loader.exec_module(migration)


class Cr2aPropertyExportsMigrationTests(unittest.TestCase):
    def test_revision_fits_alembic_version_column(self) -> None:
        self.assertLessEqual(len(migration.revision), 32)
        self.assertEqual(migration.down_revision, "0008_settlement_planning")

    def test_upgrade_creates_provider_and_delivery_tables(self) -> None:
        operations = Mock()
        with patch.object(migration, "op", operations):
            migration.upgrade()

        self.assertEqual(
            [call.args[0] for call in operations.create_table.call_args_list],
            ["export_provider_connections", "export_delivery_events"],
        )
        self.assertEqual(operations.create_index.call_count, 3)

    def test_downgrade_removes_delivery_before_provider_connections(self) -> None:
        operations = Mock()
        with patch.object(migration, "op", operations):
            migration.downgrade()

        self.assertEqual(
            [call.args[0] for call in operations.drop_table.call_args_list],
            ["export_delivery_events", "export_provider_connections"],
        )


if __name__ == "__main__":
    unittest.main()
