import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "versions"
    / "0003_material_imports.py"
)
MIGRATION_SPEC = importlib.util.spec_from_file_location("material_imports_migration", MIGRATION_PATH)
if MIGRATION_SPEC is None or MIGRATION_SPEC.loader is None:
    raise RuntimeError(f"Unable to load migration at {MIGRATION_PATH}")

migration = importlib.util.module_from_spec(MIGRATION_SPEC)
MIGRATION_SPEC.loader.exec_module(migration)


class MaterialImportsMigrationTests(unittest.TestCase):
    def test_upgrade_creates_import_batch_and_idempotency_tables(self) -> None:
        operations = Mock()
        with patch.object(migration, "op", operations):
            migration.upgrade()

        tables = {
            call.args[0]: call.args[1:]
            for call in operations.create_table.call_args_list
        }
        self.assertEqual(set(tables), {"material_import_batches", "material_import_items"})
        item_constraints = {
            item.name for item in tables["material_import_items"] if hasattr(item, "name")
        }
        self.assertIn("uq_material_import_item_batch_item", item_constraints)
        self.assertIn("uq_material_import_item_document", item_constraints)
        batch_indexes = {
            call.args[0] for call in operations.create_index.call_args_list
        }
        self.assertIn("ix_material_import_batches_user_id", batch_indexes)
        self.assertIn("ix_material_import_batches_case_id", batch_indexes)

        operations.reset_mock()
        with patch.object(migration, "op", operations):
            migration.downgrade()
        dropped_tables = [call.args[0] for call in operations.drop_table.call_args_list]
        self.assertEqual(dropped_tables, ["material_import_items", "material_import_batches"])


if __name__ == "__main__":
    unittest.main()
