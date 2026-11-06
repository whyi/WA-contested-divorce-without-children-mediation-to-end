import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

MIGRATION = Path(__file__).parents[1] / "migrations" / "versions" / "0019_attempt_finalization.py"


class AttemptFinalizationMigrationTests(unittest.TestCase):
    def test_migration_adds_only_nullable_columns_and_is_reversible(self) -> None:
        spec = importlib.util.spec_from_file_location("migration_0019", MIGRATION)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.revision, "0019_attempt_finalization")
        self.assertEqual(module.down_revision, "0018_case_delegation")
        with patch.object(module, "op") as op:
            module.upgrade()
            added = [call.args[1] for call in op.add_column.call_args_list]
            self.assertTrue(all(column.nullable for column in added))
            self.assertEqual(
                {column.name for column in added},
                {
                    "finalized_at",
                    "finalized_snapshot_json",
                    "finalized_version_ordinal",
                    "finalized_by_user_id_snapshot",
                },
            )
            op.drop_column.assert_not_called()
        with patch.object(module, "op") as op:
            module.downgrade()
            self.assertEqual(op.drop_column.call_count, 4)


if __name__ == "__main__":
    unittest.main()
